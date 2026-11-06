# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PrivacyConsent(models.Model):
    _inherit = "privacy.consent"

    log_ids = fields.One2many(
        comodel_name="privacy.consent.log",
        inverse_name="consent_id",
        string="Answer log",
    )
    accepted_changed = fields.Boolean(
        compute="_compute_accepted_changed",
        help="The acceptance has been changed in the form and not saved yet.",
    )
    collection_method_id = fields.Many2one(
        comodel_name="privacy.consent.collection.method",
        string="Collection method",
        ondelete="restrict",
        help="How the last answer recorded in the back office was collected.",
    )
    collection_note_required = fields.Boolean(
        related="collection_method_id.note_required",
    )
    collection_date = fields.Date(
        help="When the last answer recorded in the back office was collected.",
    )
    collection_note = fields.Text()
    collection_attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="privacy_consent_collection_attachment_rel",
        string="Collection attachments",
        help="Documents of the answer, for example the signed form. "
        "They are added to the chatter when the answer is saved.",
    )

    @api.depends("accepted")
    def _compute_accepted_changed(self):
        for consent in self:
            # In the form, the edited record has a new (false) id and _origin
            # is the saved record.
            consent.accepted_changed = bool(
                not consent.id
                and consent._origin
                and consent.accepted != consent._origin.accepted
            )

    @api.onchange("accepted")
    def _onchange_accepted_collection(self):
        if self.accepted_changed:
            self.collection_method_id = False
            self.collection_date = fields.Date.context_today(self)
            self.collection_note = False

    @api.constrains("collection_date")
    def _check_collection_date(self):
        today = fields.Date.context_today(self)
        for consent in self:
            if consent.collection_date and consent.collection_date > today:
                raise ValidationError(
                    self.env._("The collection date cannot be in the future.")
                )

    def _privacy_log_source(self):
        """Where the answer being written comes from."""
        context = self.env.context
        if context.get("privacy_consent_log_source"):
            return context["privacy_consent_log_source"]
        if context.get("subject_answering"):
            return "email"
        if context.get("import_file"):
            return "import"
        return "backoffice"

    def _privacy_log_vals(self, source):
        """Values of the log row for the answer just written."""
        self.ensure_one()
        context = self.env.context
        if source == "email":
            filled_by_partner = self.partner_id
            role = "subject"
        else:
            filled_by_partner = self.env.user.partner_id
            role = "employee"
        vals = {
            "consent_id": self.id,
            "partner_id": self.partner_id.id,
            "activity_id": self.activity_id.id,
            "answer": "given" if self.accepted else "refused",
            "source": source,
            "user_id": self.env.uid,
            "filled_by_partner_id": context.get(
                "privacy_consent_filled_by_partner_id", filled_by_partner.id
            ),
            "filled_by_role": context.get("privacy_consent_filled_by_role", role),
            "collection_method_id": self.collection_method_id.id,
            "collection_date": self.collection_date,
            "note": self.collection_note,
        }
        if source not in ("backoffice", "import"):
            vals.update(collection_method_id=False, collection_date=False, note=False)
        vals.update(self.env["privacy.consent.log"]._request_metadata())
        return vals

    def _check_collection_vals(self, vals):
        """A person changing an answer must say how it was collected."""
        method = self.env["privacy.consent.collection.method"].browse(
            vals.get("collection_method_id")
        )
        if not method or not vals.get("collection_date"):
            raise ValidationError(
                self.env._(
                    "To change the acceptance of a consent, indicate how and "
                    "when the answer was collected."
                )
            )
        if method.note_required and not vals.get("collection_note"):
            raise ValidationError(
                self.env._(
                    "The collection method %(method)s requires a note.",
                    method=method.display_name,
                )
            )

    @api.model
    def _privacy_command_ids(self, commands):
        """Record ids linked by many2many commands."""
        ids = []
        for command in commands or []:
            if command[0] == fields.Command.SET:
                ids = list(command[2])
            elif command[0] == fields.Command.LINK:
                ids.append(command[1])
        return ids

    def write(self, vals):
        """Log every answer; answers recorded by people become answered."""
        if "accepted" not in vals:
            return super().write(vals)
        vals = dict(vals)
        source = self._privacy_log_source()
        if source == "email":
            answered = self
        else:
            answered = self.filtered(
                lambda consent: consent.accepted != bool(vals["accepted"])
            )
            if answered and not self.env.su:
                self._check_collection_vals(vals)
                vals = dict(vals, state="answered")
        # Attachments go to the chatter message, not to the consent
        attachments = self.env["ir.attachment"].browse(
            self._privacy_command_ids(vals.pop("collection_attachment_ids", []))
            if answered
            else []
        )
        result = super().write(vals)
        if answered:
            Log = self.env["privacy.consent.log"].sudo()
            Log.create([consent._privacy_log_vals(source) for consent in answered])
            if source in ("backoffice", "import") and not self.env.su:
                answered._privacy_post_collection_message(attachments)
        return result

    def _privacy_post_collection_message(self, attachments):
        """Leave in the chatter how the answer was collected."""
        for consent in self:
            lines = [
                (
                    self.env._("Consent given")
                    if consent.accepted
                    else self.env._("Consent refused")
                ),
                self.env._(
                    "Collection method: %(method)s",
                    method=consent.collection_method_id.display_name,
                ),
                self.env._(
                    "Collection date: %(date)s",
                    date=fields.Date.to_string(consent.collection_date),
                ),
            ]
            if consent.collection_note:
                lines.append(self.env._("Note: %(note)s", note=consent.collection_note))
            body = Markup("<br/>").join(escape(line) for line in lines)
            consent.message_post(body=body, attachment_ids=attachments.ids)

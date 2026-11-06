# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request

ANSWERS = [("given", "Given"), ("refused", "Refused")]


class PrivacyConsentLog(models.Model):
    _name = "privacy.consent.log"
    _description = "Consent answer log"
    _order = "create_date desc, id desc"
    _rec_name = "partner_id"

    consent_id = fields.Many2one(
        comodel_name="privacy.consent",
        ondelete="set null",
        index=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Subject",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=True,
    )
    activity_id = fields.Many2one(
        comodel_name="privacy.activity",
        string="Activity",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=True,
    )
    res_model = fields.Char(
        string="Related document model",
        index=True,
        readonly=True,
    )
    res_id = fields.Many2oneReference(
        string="Related document",
        model_field="res_model",
        readonly=True,
    )
    answer = fields.Selection(selection=ANSWERS, required=True, readonly=True)
    confirmed = fields.Boolean(
        default=True,
        readonly=True,
        help="Answers given on a page are confirmed when the page is submitted.",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Recorded by",
        default=lambda self: self.env.user,
        readonly=True,
    )
    filled_by_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Filled in by",
        readonly=True,
    )
    filled_by_role = fields.Selection(
        selection=[
            ("subject", "Data subject"),
            ("parent", "Parent"),
            ("guardian", "Legal guardian"),
            ("employee", "Employee"),
        ],
        string="Filled in as",
        readonly=True,
    )
    source = fields.Selection(
        selection=[
            ("backoffice", "Back office"),
            ("email", "Email link"),
            ("import", "Import"),
        ],
        required=True,
        readonly=True,
    )
    ip_address = fields.Char(string="IP address", readonly=True)
    user_agent = fields.Char(string="Browser", readonly=True)
    collection_method_id = fields.Many2one(
        comodel_name="privacy.consent.collection.method",
        string="Collection method",
        ondelete="restrict",
        readonly=True,
    )
    collection_date = fields.Date(readonly=True)
    note = fields.Text(readonly=True)

    def write(self, vals):
        """Only confirming an answer is allowed, and only by the system."""
        if not self.env.su or set(vals) - {"confirmed"}:
            raise UserError(self.env._("The consent log cannot be modified."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_archiving(self):
        """Only archiving removes rows from the log."""
        if not (self.env.su and self.env.context.get("privacy_consent_log_archiving")):
            raise UserError(self.env._("The consent log cannot be deleted."))

    @api.model
    def _request_metadata(self):
        """IP address and browser of the current HTTP request, if any."""
        if not request:
            return {}
        httprequest = request.httprequest
        return {
            "ip_address": httprequest.remote_addr,
            "user_agent": httprequest.user_agent.string or False,
        }

    def _prepare_archive_vals(self):
        """Values of the archive row that keeps this log row as evidence."""
        self.ensure_one()
        partner = self.partner_id
        return {
            "partner_name": partner.name,
            "partner_email": partner.email,
            "partner_vat": partner.vat,
            "activity_name": self.activity_id.name,
            "related_document": (
                f"{self.res_model},{self.res_id}" if self.res_model else False
            ),
            "answer": self.answer,
            "answer_date": self.create_date,
            "recorded_by": self.user_id.name,
            "filled_by": self.filled_by_partner_id.name,
            "filled_by_role": self.filled_by_role,
            "source": self.source,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "collection_method": self.collection_method_id.name,
            "collection_date": self.collection_date,
            "note": self.note,
        }

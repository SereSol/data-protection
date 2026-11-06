# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError

from .privacy_consent_log import ANSWERS


class PrivacyConsentLogArchive(models.Model):
    _name = "privacy.consent.log.archive"
    _description = "Archived consent answer log"
    _order = "archive_date desc, answer_date desc, id desc"
    _rec_name = "partner_name"

    partner_name = fields.Char(string="Subject", readonly=True)
    partner_email = fields.Char(string="Email", readonly=True)
    partner_vat = fields.Char(string="Tax ID", readonly=True)
    activity_name = fields.Char(string="Activity", readonly=True)
    related_document = fields.Char(readonly=True)
    answer = fields.Selection(selection=ANSWERS, readonly=True)
    answer_date = fields.Datetime(readonly=True)
    recorded_by = fields.Char(readonly=True)
    filled_by = fields.Char(string="Filled in by", readonly=True)
    filled_by_role = fields.Selection(
        selection=lambda self: self.env["privacy.consent.log"]
        ._fields["filled_by_role"]
        ._description_selection(self.env),
        string="Filled in as",
        readonly=True,
    )
    source = fields.Selection(
        selection=lambda self: self.env["privacy.consent.log"]
        ._fields["source"]
        ._description_selection(self.env),
        readonly=True,
    )
    ip_address = fields.Char(string="IP address", readonly=True)
    user_agent = fields.Char(string="Browser", readonly=True)
    collection_method = fields.Char(readonly=True)
    collection_date = fields.Date(readonly=True)
    note = fields.Text(readonly=True)
    archive_date = fields.Date(
        default=fields.Date.context_today, readonly=True, index=True
    )
    expiry_date = fields.Date(
        readonly=True,
        index=True,
        help="The row is deleted automatically after this date. "
        "Empty: kept indefinitely.",
    )

    def write(self, vals):
        """Archived evidence cannot be changed, except by the system."""
        if not self.env.su:
            raise UserError(self.env._("The consent log archive cannot be modified."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_expired(self):
        """Only the scheduled cleanup deletes expired rows."""
        if not (self.env.su and self.env.context.get("privacy_consent_log_expiring")):
            raise UserError(self.env._("The consent log archive cannot be deleted."))

    @api.model
    def _retention_years(self):
        """Years an archived row is kept; 0 means indefinitely."""
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("privacy_consent_history.archive_retention_years")
        )
        try:
            return max(int(value or 0), 0)
        except ValueError:
            return 0

    @api.model
    def _cron_delete_expired(self):
        """Delete archived rows whose retention period is over."""
        expired = self.sudo().search(
            [("expiry_date", "!=", False), ("expiry_date", "<", fields.Date.today())]
        )
        expired.with_context(privacy_consent_log_expiring=True).unlink()

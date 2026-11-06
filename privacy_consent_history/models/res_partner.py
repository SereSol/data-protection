# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _privacy_consent_log_archive(self):
        """Move the consent log of these partners to the archive.

        The archive keeps a copy of the evidence detached from the partner,
        for example before the partner is anonymized. The rows expire after
        the retention period set in the settings.
        """
        logs = (
            self.env["privacy.consent.log"]
            .sudo()
            .search([("partner_id", "in", self.ids)])
        )
        if not logs:
            return self.env["privacy.consent.log.archive"]
        Archive = self.env["privacy.consent.log.archive"].sudo()
        years = Archive._retention_years()
        today = fields.Date.context_today(self)
        expiry_date = today + relativedelta(years=years) if years else False
        archives = Archive.create(
            [
                dict(
                    log._prepare_archive_vals(),
                    archive_date=today,
                    expiry_date=expiry_date,
                )
                for log in logs
            ]
        )
        logs.with_context(privacy_consent_log_archiving=True).unlink()
        return archives

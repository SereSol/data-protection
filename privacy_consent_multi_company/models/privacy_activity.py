# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PrivacyActivity(models.Model):
    _inherit = "privacy.activity"

    def action_new_consents(self):
        """Generate consent requests one company at a time.

        Each company's requests are created and sent in that company's
        environment, so that activities of different companies are not mixed.
        """
        consents = self.env["privacy.consent"]
        result = {}
        for company in self.company_id:
            activities = self.filtered(
                lambda act, company=company: act.company_id == company
            )
            result = super(
                PrivacyActivity, activities.with_company(company)
            ).action_new_consents()
            consents |= consents.browse(result["domain"][0][2])
        if not result:
            return super().action_new_consents()
        result["domain"] = [("id", "in", consents.ids)]
        return result

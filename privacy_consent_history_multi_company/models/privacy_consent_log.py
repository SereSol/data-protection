# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrivacyConsentLog(models.Model):
    _inherit = "privacy.consent.log"

    company_id = fields.Many2one(
        comodel_name="res.company",
        index=True,
        readonly=True,
        help="Company of the activity when the answer was recorded. "
        "It does not change if the activity is later moved to another company.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        # The company is set once, from the activity, and kept as evidence:
        # a computed field would follow later changes of the activity.
        Activity = self.env["privacy.activity"]
        for vals in vals_list:
            if vals.get("activity_id") and not vals.get("company_id"):
                activity = Activity.browse(vals["activity_id"]).sudo()
                vals["company_id"] = activity.company_id.id
        return super().create(vals_list)

    def _prepare_archive_vals(self):
        vals = super()._prepare_archive_vals()
        vals["company_id"] = self.company_id.id
        return vals

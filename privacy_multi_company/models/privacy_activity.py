# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrivacyActivity(models.Model):
    _inherit = "privacy.activity"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        tracking=True,
        help="Company that owns this data processing activity. "
        "Its contact is the controller.",
    )
    controller_id = fields.Many2one(
        compute="_compute_controller_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("company_id")
    def _compute_controller_id(self):
        for activity in self:
            activity.controller_id = activity.company_id.partner_id

    @api.model
    def _default_controller_id(self):
        """Contact of the activity's default company.

        The base module uses the user's main company, which differs from the
        activity's default company when another company is active.
        """
        company_id = self.default_get(["company_id"]).get("company_id")
        company = self.env["res.company"].browse(company_id) or self.env.company
        return company.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        # When no controller is given, use the contact of the activity's company.
        for vals in vals_list:
            if "controller_id" not in vals:
                vals["controller_id"] = (
                    self.env["res.company"].browse(vals["company_id"]).partner_id.id
                    if vals.get("company_id")
                    else self._default_controller_id().id
                )
        return super().create(vals_list)

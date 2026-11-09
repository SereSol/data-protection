# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrivacyConsentLogArchive(models.Model):
    _inherit = "privacy.consent.log.archive"

    company_id = fields.Many2one(
        comodel_name="res.company",
        index=True,
        readonly=True,
        help="Company of the archived answer. Rows archived before this module "
        "was installed have no company and are visible in every company.",
    )

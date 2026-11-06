# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    privacy_consent_archive_retention_years = fields.Integer(
        string="Consent archive retention (years)",
        config_parameter="privacy_consent_history.archive_retention_years",
        help="Years the archived consent log of an anonymized person is kept "
        "before being deleted automatically. 0: kept indefinitely.",
    )

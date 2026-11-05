# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


class ResCompany(models.Model):
    _inherit = "res.company"

    privacy_email = fields.Char(
        help="Address for data protection matters, for example the one of the "
        "data protection officer. Privacy features can use it as sender, "
        "reply-to and contact shown to data subjects.",
    )

    @api.constrains("privacy_email")
    def _check_privacy_email(self):
        for company in self:
            if company.privacy_email and not email_normalize(company.privacy_email):
                raise ValidationError(
                    self.env._(
                        "The privacy email of %(company)s is not a valid "
                        "email address.",
                        company=company.display_name,
                    )
                )

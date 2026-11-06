# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PrivacyConsentCollectionMethod(models.Model):
    _name = "privacy.consent.collection.method"
    _description = "Consent collection method"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note_required = fields.Boolean(
        help="Require a note when a consent answer is recorded with this method.",
    )

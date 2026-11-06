# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Privacy Consent Multi Company",
    "summary": "Consents follow the company of their data processing activity",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "category": "Data Protection",
    "website": "https://github.com/OCA/data-protection",
    "author": "APG23, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["privacy_consent", "privacy_multi_company"],
    "data": [
        "security/privacy_consent_multi_company_security.xml",
        "views/privacy_consent_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}

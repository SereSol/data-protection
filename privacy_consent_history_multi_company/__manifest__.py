# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Privacy Consent History Multi Company",
    "summary": "Consent log and archive rows belong to a company",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "category": "Data Protection",
    "website": "https://github.com/OCA/data-protection",
    "author": "APG23, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["privacy_consent_history", "privacy_consent_multi_company"],
    "data": [
        "security/privacy_consent_history_multi_company_security.xml",
        "views/privacy_consent_log_views.xml",
        "views/privacy_consent_log_archive_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}

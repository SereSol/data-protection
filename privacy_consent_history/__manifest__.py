# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Privacy Consent History",
    "summary": "Log of every consent answer, with IP address, browser, "
    "collection method and archive",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "category": "Data Protection",
    "website": "https://github.com/OCA/data-protection",
    "author": "APG23, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["privacy_consent"],
    "data": [
        "security/ir.model.access.csv",
        "data/privacy_consent_collection_method_data.xml",
        "data/ir_cron.xml",
        "views/privacy_consent_collection_method_views.xml",
        "views/privacy_consent_log_views.xml",
        "views/privacy_consent_log_archive_views.xml",
        "views/privacy_consent_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}

# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Privacy Multi Company",
    "summary": "Data processing activities owned by a company, "
    "with the company as controller",
    "version": "19.0.1.0.0",
    "development_status": "Alpha",
    "category": "Data Protection",
    "website": "https://github.com/OCA/data-protection",
    "author": "APG23, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["privacy"],
    "data": [
        "security/privacy_multi_company_security.xml",
        "views/privacy_activity_views.xml",
        "views/res_company_views.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "installable": True,
}

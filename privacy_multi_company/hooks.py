# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from markupsafe import Markup

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Give existing activities a company before the column becomes required.

    An activity goes to the company whose contact is its controller; when no
    company matches, it goes to the main company.
    """
    cr = env.cr
    cr.execute(
        "ALTER TABLE privacy_activity ADD COLUMN IF NOT EXISTS company_id INTEGER"
    )
    cr.execute(
        """
        UPDATE privacy_activity activity
        SET company_id = (
            SELECT MIN(company.id)
            FROM res_company company
            WHERE company.partner_id = activity.controller_id
        )
        WHERE activity.company_id IS NULL
        """
    )
    main_company = env.ref("base.main_company", raise_if_not_found=False)
    if not main_company:
        cr.execute("SELECT MIN(id) FROM res_company")
        main_company = env["res.company"].browse(cr.fetchone()[0])
    cr.execute(
        "UPDATE privacy_activity SET company_id = %s WHERE company_id IS NULL",
        (main_company.id,),
    )
    if cr.rowcount:
        _logger.info(
            "%s privacy activities without a matching company assigned to company %s",
            cr.rowcount,
            main_company.id,
        )


def post_init_hook(env):
    """Make the controller of existing activities their company's contact."""
    activities = (
        env["privacy.activity"]
        .sudo()
        .with_context(active_test=False)
        .search([])
        .filtered(lambda act: act.controller_id != act.company_id.partner_id)
    )
    for activity in activities:
        old_controller = activity.controller_id
        activity.controller_id = activity.company_id.partner_id
        activity.message_post(
            body=Markup("<p>%s</p>")
            % env._(
                "Controller changed from %(old)s to %(new)s, "
                "the contact of the activity's company.",
                old=old_controller.display_name,
                new=activity.controller_id.display_name,
            )
        )

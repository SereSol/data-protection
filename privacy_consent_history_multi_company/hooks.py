# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Give existing log rows the company of their activity."""
    env.cr.execute(
        """
        UPDATE privacy_consent_log AS log
           SET company_id = activity.company_id
          FROM privacy_activity AS activity
         WHERE activity.id = log.activity_id
           AND log.company_id IS NULL
        """
    )
    env["privacy.consent.log"].invalidate_model(["company_id"])

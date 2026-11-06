# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from email.utils import formataddr

from odoo import fields, models


class PrivacyConsent(models.Model):
    _inherit = "privacy.consent"

    company_id = fields.Many2one(
        related="activity_id.company_id",
        store=True,
        index=True,
        help="Company of the data processing activity.",
    )

    def _privacy_sender(self):
        """Formatted privacy email of the consent's company, if any."""
        self.ensure_one()
        company = self.company_id
        if not company.privacy_email:
            return False
        return formataddr((company.name, company.privacy_email))

    def _send_consent_notification(self):
        """Send from the privacy email of each consent's company, when set."""
        with_sender = self.filtered(lambda one: one._privacy_sender())
        result = super(PrivacyConsent, self - with_sender)._send_consent_notification()
        for one in with_sender.with_context(
            tpl_force_default_to=True,
            mail_notify_user_signature=False,
            mail_auto_subscribe_no_notify=True,
        ):
            sender = one._privacy_sender()
            one.with_company(one.company_id).activity_id.consent_template_id.send_mail(
                one.id, email_values={"email_from": sender, "reply_to": sender}
            )
        return result

    def action_manual_ask(self):
        """Propose the privacy email of the company as sender."""
        result = super().action_manual_ask()
        senders = {one._privacy_sender() for one in self}
        if len(senders) == 1 and False not in senders:
            sender = senders.pop()
            result["context"].update(
                {"default_email_from": sender, "default_reply_to": sender}
            )
        return result

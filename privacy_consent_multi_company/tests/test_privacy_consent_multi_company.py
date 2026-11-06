# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import Form
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestPrivacyConsentMultiCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create(
            {"name": "Company A", "privacy_email": "privacy-a@example.com"}
        )
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.companies = cls.company_a | cls.company_b
        cls.manager = new_test_user(
            cls.env,
            login="privacy_cmc_manager",
            groups="privacy.group_data_protection_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.companies.ids)],
        )
        cls.user_a = new_test_user(
            cls.env,
            login="privacy_cmc_user_a",
            groups="privacy.group_data_protection_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.subject = cls.env["res.partner"].create(
            {"name": "Consent subject", "email": "subject@example.com"}
        )
        subject_domain = repr([("id", "=", cls.subject.id)])
        Activity = cls.env["privacy.activity"]
        cls.activity_a = Activity.create(
            {
                "name": "Activity A",
                "company_id": cls.company_a.id,
                "subject_find": True,
                "subject_domain": subject_domain,
                "consent_required": "auto",
            }
        )
        cls.activity_b = Activity.create(
            {
                "name": "Activity B",
                "company_id": cls.company_b.id,
                "subject_find": True,
                "subject_domain": subject_domain,
                "consent_required": "auto",
            }
        )

    def _consents(self, user, companies):
        return (
            self.env["privacy.consent"]
            .with_user(user)
            .with_context(allowed_company_ids=companies.ids)
        )

    def _mails(self, consents):
        return self.env["mail.mail"].search(
            [("model", "=", "privacy.consent"), ("res_id", "in", consents.ids)]
        )

    def _new_consents(self):
        (self.activity_a | self.activity_b).action_new_consents()
        consent_a = self.activity_a.consent_ids
        consent_b = self.activity_b.consent_ids
        self.assertEqual(len(consent_a), 1)
        self.assertEqual(len(consent_b), 1)
        return consent_a, consent_b

    def test_consent_company_follows_activity(self):
        consent_a, consent_b = self._new_consents()
        self.assertEqual(consent_a.company_id, self.company_a)
        self.assertEqual(consent_b.company_id, self.company_b)
        self.activity_b.company_id = self.company_a
        self.assertEqual(consent_b.company_id, self.company_a)

    def test_visibility_follows_selected_companies(self):
        consent_a, consent_b = self._new_consents()
        only_a = self._consents(self.manager, self.company_a).search([])
        self.assertIn(consent_a, only_a)
        self.assertNotIn(consent_b, only_a)
        both = self._consents(self.manager, self.companies).search([])
        self.assertIn(consent_a, both)
        self.assertIn(consent_b, both)

    def test_user_without_company_access(self):
        consent_b = self._new_consents()[1]
        consents = self._consents(self.user_a, self.company_a)
        self.assertNotIn(consent_b, consents.search([]))
        with self.assertRaises(AccessError):
            consents.browse(consent_b.id).read(["state"])

    def test_partner_consent_count_follows_selection(self):
        self._new_consents()
        partners = self.env["res.partner"].with_user(self.manager)
        subject_a = partners.with_context(
            allowed_company_ids=self.company_a.ids
        ).browse(self.subject.id)
        self.assertEqual(subject_a.privacy_consent_count, 1)
        # Each request of the web client computes the count again
        self.env.invalidate_all()
        subject_both = partners.with_context(
            allowed_company_ids=self.companies.ids
        ).browse(self.subject.id)
        self.assertEqual(subject_both.privacy_consent_count, 2)

    def test_new_consents_result_lists_all_companies(self):
        result = (self.activity_a | self.activity_b).action_new_consents()
        consents = self.activity_a.consent_ids | self.activity_b.consent_ids
        self.assertEqual(result["domain"], [("id", "in", consents.ids)])

    def test_cron_generates_consents_for_each_company(self):
        # Run the scheduled code as the scheduler user, in this transaction
        cron = self.env.ref("privacy_consent.cron_auto_consent")
        self.env["privacy.activity"].with_user(cron.user_id)._cron_new_consents()
        self.assertEqual(self.activity_a.consent_ids.partner_id, self.subject)
        self.assertEqual(self.activity_b.consent_ids.partner_id, self.subject)

    def test_request_sent_from_company_privacy_email(self):
        consent_a, consent_b = self._new_consents()
        mail_a = self._mails(consent_a)
        self.assertEqual(len(mail_a), 1)
        self.assertEqual(mail_a.email_from, "Company A <privacy-a@example.com>")
        self.assertEqual(mail_a.reply_to, "Company A <privacy-a@example.com>")
        # Without a privacy email the standard sender is kept
        mail_b = self._mails(consent_b)
        self.assertEqual(len(mail_b), 1)
        self.assertNotIn("privacy-a@example.com", mail_b.email_from or "")

    def test_manual_ask_proposes_privacy_email(self):
        consent_a, consent_b = self._new_consents()
        context = consent_a.action_manual_ask()["context"]
        self.assertEqual(
            context["default_email_from"], "Company A <privacy-a@example.com>"
        )
        context = consent_b.action_manual_ask()["context"]
        self.assertNotIn("default_email_from", context)

    def test_manual_ask_composer_uses_privacy_email(self):
        consent_a = self._new_consents()[0]
        context = consent_a.action_manual_ask()["context"]
        composer = Form(self.env["mail.compose.message"].with_context(**context))
        self.assertEqual(composer.email_from, "Company A <privacy-a@example.com>")
        self.assertEqual(composer.reply_to, "Company A <privacy-a@example.com>")

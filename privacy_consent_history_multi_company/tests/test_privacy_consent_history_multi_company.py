# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon

from ..hooks import post_init_hook


@freeze_time("2026-11-09 10:00:00")
class TestPrivacyConsentHistoryMultiCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.companies = cls.company_a | cls.company_b
        cls.manager = new_test_user(
            cls.env,
            login="privacy_chmc_manager",
            groups="privacy.group_data_protection_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.companies.ids)],
        )
        cls.user_a = new_test_user(
            cls.env,
            login="privacy_chmc_user_a",
            groups="privacy.group_data_protection_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.subject = cls.env["res.partner"].create(
            {"name": "Log subject", "email": "log@example.com"}
        )
        Activity = cls.env["privacy.activity"]
        cls.activity_a = Activity.create(
            {"name": "Activity A", "company_id": cls.company_a.id}
        )
        cls.activity_b = Activity.create(
            {"name": "Activity B", "company_id": cls.company_b.id}
        )
        Consent = cls.env["privacy.consent"]
        cls.consent_a = Consent.create(
            {"partner_id": cls.subject.id, "activity_id": cls.activity_a.id}
        )
        cls.consent_b = Consent.create(
            {"partner_id": cls.subject.id, "activity_id": cls.activity_b.id}
        )
        cls.signed_form = cls.env.ref(
            "privacy_consent_history.collection_method_signed_form"
        )

    def _as(self, model, user, companies):
        return (
            self.env[model]
            .with_user(user)
            .with_context(allowed_company_ids=companies.ids)
        )

    def _accept(self, consent):
        consent.with_user(self.manager).with_context(
            allowed_company_ids=self.companies.ids
        ).write(
            {
                "accepted": True,
                "collection_method_id": self.signed_form.id,
                "collection_date": "2026-11-08",
            }
        )
        return consent.log_ids

    def test_log_company_is_the_activity_company(self):
        log_a = self._accept(self.consent_a)
        log_b = self._accept(self.consent_b)
        self.assertEqual(log_a.company_id, self.company_a)
        self.assertEqual(log_b.company_id, self.company_b)

    def test_log_company_kept_when_activity_moves(self):
        log = self._accept(self.consent_a)
        self.activity_a.company_id = self.company_b
        self.assertEqual(self.consent_a.company_id, self.company_b)
        self.assertEqual(log.company_id, self.company_a)

    def test_install_hook_fills_existing_rows(self):
        log = self._accept(self.consent_b)
        self.env.cr.execute(
            "UPDATE privacy_consent_log SET company_id = NULL WHERE id = %s",
            (log.id,),
        )
        log.invalidate_recordset(["company_id"])
        self.assertFalse(log.company_id)
        post_init_hook(self.env)
        self.assertEqual(log.company_id, self.company_b)

    def test_log_visible_in_selected_companies(self):
        log_a = self._accept(self.consent_a)
        log_b = self._accept(self.consent_b)
        Log = "privacy.consent.log"
        domain = [("partner_id", "=", self.subject.id)]
        self.assertEqual(
            self._as(Log, self.user_a, self.company_a).search(domain), log_a
        )
        self.assertEqual(
            self._as(Log, self.manager, self.company_b).search(domain), log_b
        )
        self.assertEqual(
            self._as(Log, self.manager, self.companies).search(domain),
            log_a | log_b,
        )

    def test_archive_keeps_company_and_follows_switcher(self):
        self._accept(self.consent_a)
        self._accept(self.consent_b)
        archives = self.subject._privacy_consent_log_archive()
        self.assertEqual(len(archives), 2)
        archive_a = archives.filtered(lambda one: one.activity_name == "Activity A")
        archive_b = archives - archive_a
        self.assertEqual(archive_a.company_id, self.company_a)
        self.assertEqual(archive_b.company_id, self.company_b)
        # Rows archived before the module was installed have no company.
        archive_old = (
            self.env["privacy.consent.log.archive"]
            .sudo()
            .create({"partner_name": "Old subject", "answer": "given"})
        )
        Archive = "privacy.consent.log.archive"
        all_rows = archive_a | archive_b | archive_old
        self.assertEqual(
            self._as(Archive, self.manager, self.company_a).search(
                [("id", "in", all_rows.ids)]
            ),
            archive_a | archive_old,
        )
        self.assertEqual(
            self._as(Archive, self.manager, self.companies).search(
                [("id", "in", all_rows.ids)]
            ),
            all_rows,
        )

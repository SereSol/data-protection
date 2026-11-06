# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from freezegun import freeze_time

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


@freeze_time("2026-11-06 10:00:00")
class TestPrivacyConsentHistory(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env,
            login="privacy_history_manager",
            groups="privacy.group_data_protection_manager",
        )
        cls.user = new_test_user(
            cls.env,
            login="privacy_history_user",
            groups="privacy.group_data_protection_user",
        )
        cls.subject = cls.env["res.partner"].create(
            {
                "name": "History subject",
                "email": "history@example.com",
                "vat": "IT00000000000",
            }
        )
        cls.activity = cls.env["privacy.activity"].create({"name": "History activity"})
        cls.consent = cls.env["privacy.consent"].create(
            {"partner_id": cls.subject.id, "activity_id": cls.activity.id}
        )
        cls.signed_form = cls.env.ref(
            "privacy_consent_history.collection_method_signed_form"
        )
        cls.other = cls.env.ref("privacy_consent_history.collection_method_other")

    def _consent_as(self, user):
        return self.consent.with_user(user)

    def test_backoffice_change_requires_collection(self):
        with self.assertRaises(ValidationError):
            self._consent_as(self.manager).write({"accepted": True})
        self.assertFalse(self.consent.log_ids)

    def test_backoffice_change_requires_note_when_method_asks(self):
        with self.assertRaises(ValidationError):
            self._consent_as(self.manager).write(
                {
                    "accepted": True,
                    "collection_method_id": self.other.id,
                    "collection_date": "2026-11-05",
                }
            )

    def test_backoffice_change_is_answered_and_logged(self):
        attachment = (
            self.env["ir.attachment"]
            .with_user(self.manager)
            .create({"name": "signed.pdf", "datas": base64.b64encode(b"%PDF-1.4")})
        )
        self._consent_as(self.manager).write(
            {
                "accepted": True,
                "collection_method_id": self.signed_form.id,
                "collection_date": "2026-11-03",
                "collection_note": "Signed at the front desk",
                "collection_attachment_ids": [(6, 0, attachment.ids)],
            }
        )
        self.assertEqual(self.consent.state, "answered")
        self.assertTrue(self.consent.accepted)
        log = self.consent.log_ids
        self.assertEqual(len(log), 1)
        self.assertEqual(log.answer, "given")
        self.assertEqual(log.source, "backoffice")
        self.assertEqual(log.filled_by_role, "employee")
        self.assertEqual(log.filled_by_partner_id, self.manager.partner_id)
        self.assertEqual(log.user_id, self.manager)
        self.assertEqual(log.collection_method_id, self.signed_form)
        self.assertEqual(log.collection_date, date(2026, 11, 3))
        self.assertEqual(log.note, "Signed at the front desk")
        # Date and time of the database server, not of the browser
        self.assertTrue(log.create_date)
        message = self.consent.message_ids[0]
        self.assertIn("Signed paper form", message.body)
        self.assertEqual(message.attachment_ids, attachment)
        self.assertFalse(self.consent.collection_attachment_ids)

    def test_unchanged_acceptance_is_not_logged(self):
        self._consent_as(self.manager).write({"accepted": False})
        self.assertFalse(self.consent.log_ids)

    def test_future_collection_date_refused(self):
        with self.assertRaises(ValidationError):
            self._consent_as(self.manager).write(
                {
                    "accepted": True,
                    "collection_method_id": self.signed_form.id,
                    "collection_date": "2026-11-07",
                }
            )

    def test_email_answer_is_logged(self):
        # As the public consent controller does
        self.consent.with_context(subject_answering=True).sudo().action_answer(
            True, "metadata"
        )
        log = self.consent.log_ids
        self.assertEqual(len(log), 1)
        self.assertEqual(log.source, "email")
        self.assertEqual(log.filled_by_role, "subject")
        self.assertEqual(log.filled_by_partner_id, self.subject)
        self.assertFalse(log.collection_method_id)
        # Every answer of the subject is logged, also an unchanged one
        self.consent.with_context(subject_answering=True).sudo().action_answer(
            True, "metadata"
        )
        self.assertEqual(len(self.consent.log_ids), 2)

    def test_import_requires_collection(self):
        consent = self._consent_as(self.manager).with_context(import_file=True)
        with self.assertRaises(ValidationError):
            consent.write({"accepted": True})
        consent.write(
            {
                "accepted": True,
                "collection_method_id": self.signed_form.id,
                "collection_date": "2026-11-01",
            }
        )
        self.assertEqual(self.consent.log_ids.source, "import")

    def test_form_unlocks_collection_fields(self):
        with Form(self._consent_as(self.manager)) as form:
            self.assertFalse(form.accepted_changed)
            form.accepted = True
            self.assertTrue(form.accepted_changed)
            self.assertEqual(str(form.collection_date), "2026-11-06")
            form.collection_method_id = self.signed_form
        self.assertEqual(self.consent.state, "answered")
        self.assertEqual(self.consent.log_ids.collection_method_id, self.signed_form)

    def _log_answer(self):
        self._consent_as(self.manager).write(
            {
                "accepted": True,
                "collection_method_id": self.signed_form.id,
                "collection_date": "2026-11-06",
            }
        )
        return self.consent.log_ids

    def test_log_cannot_be_changed_by_users(self):
        log = self._log_answer()
        with self.assertRaises(UserError):
            log.with_user(self.manager).write({"answer": "refused"})
        with self.assertRaises(AccessError):
            log.with_user(self.manager).unlink()
        with self.assertRaises(UserError):
            log.sudo().write({"answer": "refused"})
        with self.assertRaises(UserError):
            log.sudo().unlink()
        log.sudo().write({"confirmed": False})
        self.assertFalse(log.confirmed)

    def test_user_reads_log_not_archive(self):
        log = self._log_answer()
        log.with_user(self.user).read(["answer"])
        with self.assertRaises(AccessError):
            self.env["privacy.consent.log.archive"].with_user(self.user).search([])

    def test_archive_and_expiry(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "privacy_consent_history.archive_retention_years", "5"
        )
        self._log_answer()
        archives = self.subject._privacy_consent_log_archive()
        self.assertFalse(self.consent.log_ids)
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives.partner_name, "History subject")
        self.assertEqual(archives.partner_email, "history@example.com")
        self.assertEqual(archives.partner_vat, "IT00000000000")
        self.assertEqual(archives.activity_name, "History activity")
        self.assertEqual(archives.answer, "given")
        self.assertEqual(archives.collection_method, "Signed paper form")
        self.assertEqual(archives.expiry_date, date(2031, 11, 6))
        with self.assertRaises(UserError):
            archives.with_user(self.manager).write({"answer": "refused"})
        with self.assertRaises(AccessError):
            archives.with_user(self.manager).unlink()
        with self.assertRaises(UserError):
            archives.unlink()
        Archive = self.env["privacy.consent.log.archive"]
        with freeze_time("2031-11-06"):
            Archive._cron_delete_expired()
            self.assertTrue(archives.exists())
        with freeze_time("2031-11-07"):
            Archive._cron_delete_expired()
            self.assertFalse(archives.exists())

    def test_archive_without_retention_never_expires(self):
        self._log_answer()
        archives = self.subject._privacy_consent_log_archive()
        self.assertFalse(archives.expiry_date)

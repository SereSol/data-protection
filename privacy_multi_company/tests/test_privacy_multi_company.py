# Copyright 2026 APG23
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon

from ..hooks import post_init_hook


class TestPrivacyMultiCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.manager = new_test_user(
            cls.env,
            login="privacy_mc_manager",
            groups="privacy.group_data_protection_manager",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )
        cls.user_a = new_test_user(
            cls.env,
            login="privacy_mc_user_a",
            groups="privacy.group_data_protection_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        Activity = cls.env["privacy.activity"]
        cls.activity_a = Activity.create(
            {"name": "Activity A", "company_id": cls.company_a.id}
        )
        cls.activity_b = Activity.create(
            {"name": "Activity B", "company_id": cls.company_b.id}
        )

    def _activities(self, user, companies):
        return (
            self.env["privacy.activity"]
            .with_user(user)
            .with_context(allowed_company_ids=companies.ids)
        )

    def test_default_company_and_controller(self):
        activity = self._activities(self.manager, self.company_a).create(
            {"name": "Default company"}
        )
        self.assertEqual(activity.company_id, self.company_a)
        self.assertEqual(activity.controller_id, self.company_a.partner_id)

    def test_controller_follows_given_company(self):
        # The user's main company is A, the activity belongs to B
        activity = self._activities(
            self.manager, self.company_a | self.company_b
        ).create({"name": "Other company", "company_id": self.company_b.id})
        self.assertEqual(activity.controller_id, self.company_b.partner_id)

    def test_controller_follows_company_change(self):
        self.activity_a.company_id = self.company_b
        self.assertEqual(self.activity_a.controller_id, self.company_b.partner_id)

    def test_visibility_follows_selected_companies(self):
        only_a = self._activities(self.manager, self.company_a).search([])
        self.assertIn(self.activity_a, only_a)
        self.assertNotIn(self.activity_b, only_a)
        both = self._activities(self.manager, self.company_a | self.company_b).search(
            []
        )
        self.assertIn(self.activity_a, both)
        self.assertIn(self.activity_b, both)

    def test_user_without_company_access(self):
        activities = self._activities(self.user_a, self.company_a)
        self.assertNotIn(self.activity_b, activities.search([]))
        with self.assertRaises(AccessError):
            activities.browse(self.activity_b.id).read(["name"])

    def test_privacy_email(self):
        self.company_a.privacy_email = "privacy@example.com"
        self.assertEqual(self.company_a.privacy_email, "privacy@example.com")
        with self.assertRaises(ValidationError):
            self.company_b.privacy_email = "not an email"

    def test_post_init_hook_fixes_controller(self):
        other = self.env["res.partner"].create({"name": "Other controller"})
        self.activity_a.controller_id = other
        post_init_hook(self.env)
        self.assertEqual(self.activity_a.controller_id, self.company_a.partner_id)
        self.assertIn("Other controller", self.activity_a.message_ids[0].body)
        # Activities already consistent are left untouched
        self.assertFalse(
            self.activity_b.message_ids.filtered(
                lambda msg: "Controller changed" in (msg.body or "")
            )
        )

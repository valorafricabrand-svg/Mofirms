import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

DEV_NOTICE = "running in local development"


class TemplateAssetPathTests(SimpleTestCase):
    def test_templates_do_not_hardcode_debug_only_asset_paths(self):
        # /css/ and /js/ are only routed when DEBUG is on; production serves /static/.
        pattern = re.compile(r'(?:href|src)="/(?:css|js)/')
        offenders = [
            str(path.relative_to(settings.BASE_DIR))
            for app in ("farmers", "smart_hasibu")
            for path in (settings.BASE_DIR / app / "templates").rglob("*.html")
            if pattern.search(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])


class DevelopmentNoticeTests(TestCase):
    def test_notice_shown_outside_production(self):
        response = self.client.get(reverse("register_farmer"))
        self.assertContains(response, DEV_NOTICE)

    @override_settings(DJANGO_ENVIRONMENT="production", DEBUG=False, DEMO_MODE=False)
    def test_notice_hidden_in_production(self):
        response = self.client.get(reverse("register_farmer"))
        self.assertNotContains(response, DEV_NOTICE)
        self.assertContains(response, "/static/css/style")

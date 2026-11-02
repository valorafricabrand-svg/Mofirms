from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from mofirms_backend.middleware import DemoReadOnlyMiddleware


@override_settings(DEMO_MODE=True)
class DemoReadOnlyMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = DemoReadOnlyMiddleware(lambda request: HttpResponse("ok"))

    def test_get_requests_are_allowed(self):
        response = self.middleware(self.factory.get("/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_post_requests_are_rejected_without_processing(self):
        response = self.middleware(self.factory.post("/portal/register/", {"name": "test"}))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET, HEAD, OPTIONS")
        self.assertIn(b"submissions and uploads are disabled", response.content)

    def test_application_rejects_submission_requests_in_demo_mode(self):
        response = self.client.post(
            "/portal/register/", {"full_name": "test"}, secure=True
        )

        self.assertEqual(response.status_code, 405)
        self.assertIn(b"submissions and uploads are disabled", response.content)

    @override_settings(DEMO_MODE=False)
    def test_writes_are_unchanged_outside_demo_mode(self):
        response = self.middleware(self.factory.post("/portal/register/"))

        self.assertEqual(response.status_code, 200)

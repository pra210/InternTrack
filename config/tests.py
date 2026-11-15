from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from config.views import server_error


class ProductionErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_404_uses_a_generic_page_without_a_traceback(self):
        response = self.client.get('/this-page-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            'We can’t find that page.',
            status_code=404,
        )
        self.assertNotContains(response, 'Traceback', status_code=404)

    @override_settings(DEBUG=False)
    def test_403_uses_a_generic_page_for_nonstaff_dashboard_access(self):
        student = User.objects.create_user(
            username='errorstudent',
            email='errorstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        self.client.force_login(student)

        response = self.client.get(reverse('platform_admin:dashboard'))

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            'This page isn’t available to your account.',
            status_code=403,
        )
        self.assertNotContains(response, 'Traceback', status_code=403)

    def test_500_page_is_generic_and_does_not_depend_on_site_assets(self):
        request = RequestFactory().get('/unexpected-error/')

        response = server_error(request)

        self.assertEqual(response.status_code, 500)
        self.assertContains(
            response,
            'We couldn’t complete that request.',
            status_code=500,
        )
        self.assertNotContains(response, 'Traceback', status_code=500)

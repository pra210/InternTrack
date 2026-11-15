from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User


class StudentAuthTests(TestCase):
    def test_student_registration_creates_account_and_profile(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'newstudent',
                'email': 'newstudent@example.com',
                'full_name': 'New Student',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(username='newstudent', role=User.Role.STUDENT).exists(),
        )
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_student_login_requires_student_role(self):
        User.objects.create_user(
            username='companyuser',
            email='company@example.com',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'companyuser', 'password': 'StrongPass123!'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_student_registration_rejects_weak_passwords(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'username': 'weakpasswordstudent',
                'email': 'weakpasswordstudent@example.com',
                'full_name': 'Weak Password Student',
                'password1': 'password',
                'password2': 'password',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('password1', response.context['form'].errors)
        self.assertFalse(
            User.objects.filter(username='weakpasswordstudent').exists(),
        )

    @override_settings(
        AXES_FAILURE_LIMIT=2,
        AXES_COOLOFF_TIME=0.5,
        AXES_USE_ATTEMPT_EXPIRATION=True,
        AXES_LOCKOUT_PARAMETERS=['ip_address'],
    )
    def test_login_throttle_is_ip_based_and_legitimate_login_still_works(self):
        user = User.objects.create_user(
            username='throttledstudent',
            email='throttledstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        login_url = reverse('accounts:login')

        first_failure = self.client.post(
            login_url,
            {
                'username': 'unknown-account-one',
                'password': 'WrongPassword123!',
            },
        )
        self.assertEqual(first_failure.status_code, 200)

        lockout_response = self.client.post(
            login_url,
            {
                'username': 'unknown-account-two',
                'password': 'WrongPassword123!',
            },
        )
        self.assertEqual(lockout_response.status_code, 429)

        locked_response = self.client.post(
            login_url,
            {'username': user.username, 'password': 'WrongPassword123!'},
        )
        self.assertEqual(locked_response.status_code, 429)

        valid_response = self.client.post(
            login_url,
            {
                'username': user.username,
                'password': 'StrongStudent123!',
            },
            REMOTE_ADDR='192.0.2.25',
        )
        self.assertRedirects(
            valid_response,
            reverse('dashboard:student_dashboard'),
        )


class CsrfAuthenticationTests(TestCase):
    def test_login_rejects_missing_and_invalid_csrf_tokens_and_accepts_valid_token(self):
        user = User.objects.create_user(
            username='csrfstudent',
            email='csrfstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        client = Client(enforce_csrf_checks=True)
        login_url = reverse('accounts:login')
        credentials = {
            'username': user.username,
            'password': 'StrongStudent123!',
        }

        missing_token_response = client.post(login_url, credentials)
        self.assertEqual(missing_token_response.status_code, 403)

        invalid_token_response = client.post(
            login_url,
            credentials,
            HTTP_X_CSRFTOKEN='invalid-token',
        )
        self.assertEqual(invalid_token_response.status_code, 403)

        client.get(login_url)
        csrf_token = client.cookies['csrftoken'].value
        valid_token_response = client.post(
            login_url,
            credentials,
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertRedirects(
            valid_token_response,
            reverse('dashboard:student_dashboard'),
        )

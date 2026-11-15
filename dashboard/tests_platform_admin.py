"""Tests for the protected platform administration dashboard."""

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from applications.models import Application
from companies.models import CompanyProfile
from internships.models import Internship
from students.models import StudentProfile


class PlatformAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='platformadmin',
            email='platformadmin@example.com',
            password='StrongAdmin123!',
        )
        self.student_user = User.objects.create_user(
            username='platformstudent',
            email='platformstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            full_name='Platform Student',
            college='Example College',
            department='Computer Science',
        )
        self.company_user = User.objects.create_user(
            username='platformcompany',
            email='platformcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Platform Company',
            contact_person='Casey Recruiter',
            location='Chennai',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Platform Developer Intern',
            description='Build platform features.',
            location='Chennai',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )
        self.application = Application.objects.create(
            student=self.student,
            internship=self.internship,
        )

    def test_platform_dashboard_is_staff_only_and_shows_real_statistics(self):
        url = reverse('platform_admin:dashboard')
        response = self.client.get(url)
        self.assertRedirects(
            response,
            f'{reverse("platform_admin:login")}?next={url}',
        )

        self.client.force_login(self.student_user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.company_user)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_companies'], 1)
        self.assertEqual(response.context['total_internships'], 1)
        self.assertEqual(response.context['total_applications'], 1)
        self.assertEqual(response.context['pending_applications'], 1)
        self.assertContains(response, 'Platform Student applied for')

    def test_platform_login_rejects_nonstaff_and_accepts_staff_credentials(self):
        login_url = reverse('platform_admin:login')
        response = self.client.post(
            login_url,
            {
                'username': self.student_user.username,
                'password': 'StrongStudent123!',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'platform administrators only')
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(
            login_url,
            {
                'username': self.admin.username,
                'password': 'StrongAdmin123!',
            },
        )
        self.assertRedirects(response, reverse('platform_admin:dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.admin.pk)

    def test_student_and_company_search_and_active_filters(self):
        another_student = User.objects.create_user(
            username='inactiveplatformstudent',
            email='inactiveplatformstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
            is_active=False,
        )
        StudentProfile.objects.create(
            user=another_student,
            full_name='Inactive Platform Student',
            college='Other College',
        )
        inactive_company_user = User.objects.create_user(
            username='inactiveplatformcompany',
            email='inactiveplatformcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
            is_active=False,
        )
        CompanyProfile.objects.create(
            user=inactive_company_user,
            company_name='Inactive Platform Company',
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('platform_admin:students'),
            {'q': 'Example College', 'active': 'active'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform Student')
        self.assertNotContains(response, 'Inactive Platform Student')

        response = self.client.get(
            reverse('platform_admin:companies'),
            {'q': 'Chennai', 'active': 'active'},
        )
        self.assertContains(response, 'Platform Company')
        self.assertNotContains(response, 'Inactive Platform Company')

        response = self.client.get(
            reverse('platform_admin:companies'),
            {'active': 'inactive'},
        )
        self.assertContains(response, 'Inactive Platform Company')

    def test_internship_status_actions_and_protected_delete(self):
        self.client.force_login(self.admin)
        list_url = reverse('platform_admin:internships')
        response = self.client.get(
            list_url,
            {'q': 'Platform Developer', 'status': Internship.Status.OPEN},
        )
        self.assertContains(response, 'Platform Developer Intern')

        response = self.client.post(
            reverse(
                'platform_admin:internship_status_update',
                args=[self.internship.pk, 'deactivate'],
            ),
        )
        self.assertRedirects(response, list_url)
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.status, Internship.Status.CLOSED)

        self.client.post(
            reverse(
                'platform_admin:internship_status_update',
                args=[self.internship.pk, 'activate'],
            ),
        )
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.status, Internship.Status.OPEN)

        response = self.client.post(
            reverse('platform_admin:internship_delete', args=[self.internship.pk]),
            follow=True,
        )
        self.assertContains(response, 'cannot be deleted')
        self.assertTrue(Internship.objects.filter(pk=self.internship.pk).exists())
        self.assertTrue(Application.objects.filter(pk=self.application.pk).exists())

        unprotected = Internship.objects.create(
            company=self.company,
            title='Unused Internship',
            description='No applications.',
            location='Remote',
            duration='2 months',
            deadline='2030-01-02',
        )
        response = self.client.post(
            reverse('platform_admin:internship_delete', args=[unprotected.pk]),
        )
        self.assertRedirects(response, list_url)
        self.assertFalse(Internship.objects.filter(pk=unprotected.pk).exists())

    def test_internship_actions_require_specific_django_permissions(self):
        limited_admin = User.objects.create_user(
            username='limitedplatformadmin',
            email='limitedplatformadmin@example.com',
            password='StrongLimited123!',
            is_staff=True,
        )
        permission = Permission.objects.get(
            content_type__app_label='internships',
            codename='view_internship',
        )
        limited_admin.user_permissions.add(permission)
        self.client.force_login(limited_admin)

        response = self.client.get(reverse('platform_admin:internships'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse(
                'platform_admin:internship_status_update',
                args=[self.internship.pk, 'deactivate'],
            ),
        )
        self.assertEqual(response.status_code, 403)
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.status, Internship.Status.OPEN)

    def test_application_monitoring_filters_by_status_and_search(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('platform_admin:applications'),
            {'q': 'Platform Developer', 'status': Application.Status.PENDING},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform Student')
        self.assertContains(response, 'Platform Developer Intern')

        self.application.status = Application.Status.REJECTED
        self.application.save(update_fields=['status'])
        response = self.client.get(
            reverse('platform_admin:applications'),
            {'status': Application.Status.PENDING},
        )
        self.assertNotContains(response, 'Platform Student')

    def test_platform_management_logout_requires_post(self):
        self.client.force_login(self.admin)
        logout_url = reverse('platform_admin:logout')
        self.assertEqual(self.client.get(logout_url).status_code, 405)
        response = self.client.post(logout_url)
        self.assertRedirects(response, reverse('platform_admin:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Notification, User
from companies.models import CompanyProfile
from internships.models import Internship
from students.models import Skill, StudentProfile

from .models import Application


class ApplicationRelationshipTests(TestCase):
    def setUp(self):
        student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongPass123!',
            role=User.Role.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=student_user,
            full_name='Sample Student',
        )
        company_user = User.objects.create_user(
            username='company',
            email='company@example.com',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=company_user,
            company_name='Example Company',
        )
        self.internship = Internship.objects.create(
            company=company,
            title='Software Intern',
            description='Build and test software.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )

    def test_application_relationships_and_unique_pair(self):
        application = Application.objects.create(
            student=self.student,
            internship=self.internship,
        )
        self.assertEqual(self.student.applications.get(), application)
        self.assertEqual(self.internship.applications.get(), application)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(
                    student=self.student,
                    internship=self.internship,
                )

    def test_internship_required_skills_and_notification_relationship(self):
        skill = Skill.objects.create(name='Django')
        self.internship.required_skills.add(skill)
        self.assertIn(skill, self.internship.required_skills.all())

        notification = Notification.objects.create(
            user=self.student.user,
            message='Your application was received.',
        )
        self.assertEqual(self.student.user.notifications.get(), notification)


class StudentApplicationWorkflowTests(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user(
            username='workflowcompany',
            email='workflowcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        self.company = CompanyProfile.objects.create(
            user=self.company_user,
            company_name='Workflow Company',
            description='A company for application workflow tests.',
            website='https://example.com',
            location='Remote',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Python Django Developer Intern',
            description='Build helpful web applications.',
            location='Remote',
            stipend=1500,
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )
        self.student_user = User.objects.create_user(
            username='workflowstudent',
            email='workflowstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            full_name='Workflow Student',
        )
        self.detail_url = reverse(
            'internships:detail',
            args=[self.internship.pk],
        )
        self.apply_url = reverse(
            'applications:apply',
            args=[self.internship.pk],
        )

    def test_internship_details_include_role_company_and_apply_action(self):
        Skill.objects.create(name='Django')
        self.internship.required_skills.add(Skill.objects.get(name='Django'))

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Django Developer Intern')
        self.assertContains(response, 'Workflow Company')
        self.assertContains(response, 'Build helpful web applications.')
        self.assertContains(response, 'Django')
        self.assertContains(response, 'Remote')
        self.assertContains(response, '3 months')
        self.assertContains(response, '1500')
        self.assertContains(response, 'Apply Now')

    def test_application_requires_login_and_login_returns_to_apply_form(self):
        response = self.client.get(self.apply_url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.apply_url}",
        )
        response = self.client.get(response.url)
        self.assertContains(response, f'value="{self.apply_url}"')

        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': self.student_user.username,
                'password': 'StrongStudent123!',
                'next': self.apply_url,
            },
        )
        self.assertRedirects(response, self.apply_url)
        self.assertEqual(Application.objects.count(), 0)

    def test_student_can_submit_a_valid_application(self):
        self.client.force_login(self.student_user)

        response = self.client.post(
            self.apply_url,
            {'cover_letter': 'I am excited to build Django applications.'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Application.objects.filter(
                student=self.student,
                internship=self.internship,
                cover_letter='I am excited to build Django applications.',
            ).exists(),
        )
        notification = Notification.objects.get(user=self.student_user)
        self.assertIn('application', notification.message)
        self.assertContains(response, 'submitted successfully')
        self.assertContains(response, 'Python Django Developer Intern')

    def test_cover_letter_is_required_and_must_be_meaningful(self):
        self.client.force_login(self.student_user)

        response = self.client.post(self.apply_url, {'cover_letter': 'Too short'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'at least 20 characters')
        self.assertEqual(Application.objects.count(), 0)

    def test_duplicate_application_is_blocked(self):
        Application.objects.create(
            student=self.student,
            internship=self.internship,
            cover_letter='An existing application introduction.',
        )
        self.client.force_login(self.student_user)

        response = self.client.post(
            self.apply_url,
            {'cover_letter': 'I would like to apply again for this role.'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already applied')
        self.assertEqual(Application.objects.filter(
            student=self.student,
            internship=self.internship,
        ).count(), 1)

    def test_company_cannot_submit_student_application(self):
        self.client.force_login(self.company_user)

        response = self.client.post(
            self.apply_url,
            {'cover_letter': 'I am interested in applying to this position.'},
        )

        self.assertRedirects(response, self.detail_url)
        self.assertEqual(Application.objects.count(), 0)

    def test_closed_and_expired_internships_reject_applications(self):
        self.client.force_login(self.student_user)
        for status, deadline in (
            (Internship.Status.CLOSED, '2030-01-01'),
            (Internship.Status.OPEN, '2020-01-01'),
        ):
            with self.subTest(status=status, deadline=deadline):
                self.internship.status = status
                self.internship.deadline = deadline
                self.internship.save()

                response = self.client.post(
                    self.apply_url,
                    {'cover_letter': 'I am interested in applying to this position.'},
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'no longer accepting applications')
                self.assertFalse(
                    Application.objects.filter(
                        student=self.student,
                        internship=self.internship,
                    ).exists(),
                )

    def test_details_show_closed_status_without_apply_button(self):
        self.internship.status = Internship.Status.CLOSED
        self.internship.save()

        response = self.client.get(self.detail_url)

        self.assertContains(response, 'Closed')
        self.assertContains(response, 'no longer accepting applications')
        self.assertNotContains(response, 'Apply Now')

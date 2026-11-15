from django.test import TestCase
from django.urls import reverse

from accounts.models import Notification, User
from applications.models import Application
from companies.models import CompanyProfile
from internships.models import Internship
from students.models import Skill, StudentProfile


class HomePageTests(TestCase):
    def test_homepage_renders_landing_sections_and_live_counts(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Find the work that')
        self.assertContains(response, 'From searching to starting')
        self.assertContains(response, 'There are no open internships to show right now.')
        self.assertEqual(response.context['student_count'], 0)
        self.assertEqual(response.context['internship_count'], 0)

    def test_search_filters_open_internships_by_skill(self):
        user = User.objects.create_user(
            username='company',
            email='company@example.com',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=user,
            company_name='Example Studio',
        )
        internship = Internship.objects.create(
            company=company,
            title='Junior Developer',
            description='Build useful tools.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )
        skill = Skill.objects.create(name='Python')
        internship.required_skills.add(skill)

        response = self.client.get(reverse('home'), {'q': 'python'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Junior Developer')
        self.assertEqual(
            list(response.context['internships']),
            [internship],
        )

    def test_multiword_search_matches_terms_across_internship_fields(self):
        user = User.objects.create_user(
            username='technova',
            email='recruiter@technova.example',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=user,
            company_name='TechNova Solutions',
        )
        internship = Internship.objects.create(
            company=company,
            title='Python Django Developer Intern',
            description='Build and maintain web applications.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )
        internship.required_skills.add(Skill.objects.create(name='Django'))
        skill_match = Internship.objects.create(
            company=company,
            title='Python Developer',
            description='Build and maintain web applications.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-02',
            status=Internship.Status.OPEN,
        )
        skill_match.required_skills.add(Skill.objects.get(name='Django'))
        Internship.objects.create(
            company=company,
            title='Python Developer',
            description='Python programming role.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )

        response = self.client.get(reverse('home'), {'q': 'Python Django'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['internships']),
            {internship, skill_match},
        )
        self.assertEqual(response.context['search_result_count'], 2)
        self.assertContains(response, 'id="search-results"')
        self.assertContains(response, 'value="Python Django"')
        self.assertContains(response, 'Clear search')

    def test_search_includes_all_matches_and_clear_restores_open_roles(self):
        user = User.objects.create_user(
            username='manyroles',
            email='manyroles@example.com',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=user,
            company_name='Many Roles Inc',
        )
        matches = [
            Internship.objects.create(
                company=company,
                title=f'Python role {index}',
                description='A role for Python developers.',
                location='Remote',
                duration='3 months',
                deadline=f'2030-01-{index:02d}',
                status=Internship.Status.OPEN,
            )
            for index in range(1, 5)
        ]
        Internship.objects.create(
            company=company,
            title='Closed Python role',
            description='Python developer.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-05',
            status=Internship.Status.CLOSED,
        )

        response = self.client.get(reverse('home'), {'q': 'Python'})

        self.assertEqual(response.context['search_result_count'], 4)
        self.assertEqual(set(response.context['internships']), set(matches))

        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['query'], '')
        self.assertEqual(response.context['search_result_count'], 4)
        self.assertEqual(len(response.context['internships']), 3)
        self.assertContains(response, 'Explore open opportunities')

    def test_search_shows_clear_no_match_state(self):
        response = self.client.get(reverse('home'), {'q': 'NoSuchRole987'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_result_count'], 0)
        self.assertContains(response, 'No matching internships found')
        self.assertContains(response, 'Clear search and browse all opportunities')


class StudentDashboardTests(TestCase):
    def test_student_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:student_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_company_cannot_access_student_dashboard_by_url(self):
        company_user = User.objects.create_user(
            username='dashboardcompany',
            email='dashboardcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        self.client.force_login(company_user)

        response = self.client.get(reverse('dashboard:student_dashboard'))

        self.assertRedirects(response, reverse('home'))

    def test_student_dashboard_shows_own_application_history_and_status_counts(self):
        student_user = User.objects.create_user(
            username='dashboardstudent',
            email='dashboardstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Dashboard Student',
        )
        company_user = User.objects.create_user(
            username='dashboardcompany',
            email='dashboardcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=company_user,
            company_name='Dashboard Company',
        )
        statuses = [
            Application.Status.PENDING,
            Application.Status.REVIEWING,
            Application.Status.SHORTLISTED,
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
        ]
        applications = []
        for index, status in enumerate(statuses):
            internship = Internship.objects.create(
                company=company,
                title=f'Dashboard role {index}',
                description='A dashboard test role.',
                location='Remote',
                duration='3 months',
                deadline=f'2030-01-{index + 1:02d}',
                status=Internship.Status.OPEN,
            )
            applications.append(
                Application.objects.create(
                    student=student,
                    internship=internship,
                    status=status,
                )
            )

        other_user = User.objects.create_user(
            username='otherstudent',
            email='otherstudent@example.com',
            password='StrongOther123!',
            role=User.Role.STUDENT,
        )
        other_student = StudentProfile.objects.create(
            user=other_user,
            full_name='Other Student',
        )
        Application.objects.create(
            student=other_student,
            internship=applications[0].internship,
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('dashboard:student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_applications'], 5)
        self.assertEqual(
            response.context['application_page'].paginator.count,
            5,
        )
        self.assertEqual(response.context['status_counts']['PENDING'], 1)
        self.assertEqual(response.context['status_counts']['REVIEWING'], 1)
        self.assertEqual(response.context['status_counts']['SHORTLISTED'], 1)
        self.assertEqual(response.context['status_counts']['ACCEPTED'], 1)
        self.assertEqual(response.context['status_counts']['REJECTED'], 1)
        self.assertEqual(
            set(response.context['applications']),
            set(applications),
        )
        self.assertContains(response, 'Dashboard role 0')
        self.assertContains(response, 'Shortlisted')
        self.assertContains(response, 'Interviewing')
        self.assertContains(response, 'Rejected')
        self.assertNotContains(response, 'Other Student')

    def test_student_application_history_is_paginated(self):
        student_user = User.objects.create_user(
            username='paginatedstudent',
            email='paginatedstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Paginated Student',
        )
        company_user = User.objects.create_user(
            username='paginationcompany',
            email='paginationcompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        company = CompanyProfile.objects.create(
            user=company_user,
            company_name='Pagination Company',
        )
        for index in range(11):
            internship = Internship.objects.create(
                company=company,
                title=f'Pagination role {index}',
                description='A pagination test role.',
                location='Remote',
                duration='3 months',
                deadline=f'2030-02-{index + 1:02d}',
                status=Internship.Status.OPEN,
            )
            Application.objects.create(student=student, internship=internship)

        self.client.force_login(student_user)
        response = self.client.get(reverse('dashboard:student_dashboard'))

        self.assertEqual(response.context['total_applications'], 11)
        self.assertEqual(len(response.context['applications']), 10)
        self.assertEqual(
            response.context['application_page'].paginator.num_pages,
            2,
        )
        response = self.client.get(
            reverse('dashboard:student_dashboard'),
            {'page': 2},
        )
        self.assertEqual(len(response.context['applications']), 1)

    def test_student_can_review_and_mark_only_their_own_notifications_read(self):
        student_user = User.objects.create_user(
            username='notificationstudent',
            email='notificationstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        other_user = User.objects.create_user(
            username='othernotificationstudent',
            email='othernotificationstudent@example.com',
            password='StrongOther123!',
            role=User.Role.STUDENT,
        )
        notification = Notification.objects.create(
            user=student_user,
            message='Your application was shortlisted.',
        )
        other_notification = Notification.objects.create(
            user=other_user,
            message='Private notification.',
        )
        self.client.force_login(student_user)

        response = self.client.get(reverse('dashboard:student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unread_notification_count'], 1)
        self.assertContains(response, 'Your application was shortlisted.')
        self.assertContains(response, '1 unread')
        self.assertEqual(
            self.client.get(
                reverse(
                    'dashboard:mark_notification_read',
                    args=[notification.pk],
                ),
            ).status_code,
            405,
        )

        response = self.client.post(
            reverse(
                'dashboard:mark_notification_read',
                args=[notification.pk],
            ),
        )
        self.assertRedirects(response, reverse('dashboard:student_dashboard'))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        response = self.client.post(
            reverse(
                'dashboard:mark_notification_read',
                args=[other_notification.pk],
            ),
        )
        self.assertEqual(response.status_code, 404)

import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Notification, User
from applications.models import (
    Application,
    ApplicationStatusHistory,
    Interview,
)
from internships.models import Internship
from students.models import StudentProfile

from .models import CompanyProfile


class CompanyProfileTests(TestCase):
    def test_company_profile_requires_company_role(self):
        user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongPass123!',
            role=User.Role.STUDENT,
        )
        profile = CompanyProfile(
            user=user,
            company_name='Not a company account',
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()


class CompanyRecruiterFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='recruiter',
            email='recruiter@example.com',
            password='StrongRecruiter123!',
            role=User.Role.COMPANY,
        )
        self.company = CompanyProfile.objects.create(
            user=self.user,
            company_name='Example Company',
            contact_person='Alex Recruiter',
            phone='+1 555 123 4567',
            website='https://example.com',
            location='Remote',
            description='A sample company.',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Intern',
            description='Help build software.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )

    def test_company_registration_creates_role_profile_and_hashed_password(self):
        response = self.client.post(
            reverse('companies:register'),
            {
                'company_name': 'New Company',
                'email': 'new@example.com',
                'username': 'newrecruiter',
                'contact_person': 'Pat Recruiter',
                'phone': '+1 555 000 1111',
                'website': 'https://new.example.com',
                'location': 'New York',
                'description': 'A growing company.',
                'password1': 'StrongRecruiter123!',
                'password2': 'StrongRecruiter123!',
            },
        )

        self.assertRedirects(response, reverse('companies:dashboard'))
        user = User.objects.get(username='newrecruiter')
        self.assertEqual(user.role, User.Role.COMPANY)
        self.assertTrue(user.check_password('StrongRecruiter123!'))
        self.assertEqual(user.company_profile.contact_person, 'Pat Recruiter')
        self.assertEqual(user.company_profile.phone, '+1 555 000 1111')

    def test_registration_rejects_duplicate_username_and_email(self):
        response = self.client.post(
            reverse('companies:register'),
            {
                'company_name': 'Another Company',
                'email': self.user.email,
                'username': self.user.username,
                'contact_person': 'A Person',
                'phone': '1234567890',
                'website': 'https://another.example.com',
                'location': 'Remote',
                'description': 'Description.',
                'password1': 'StrongRecruiter123!',
                'password2': 'StrongRecruiter123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_mismatched_and_weak_passwords(self):
        data = {
            'company_name': 'Another Company',
            'email': 'another@example.com',
            'username': 'anotherrecruiter',
            'contact_person': 'A Person',
            'phone': '1234567890',
            'website': 'https://another.example.com',
            'location': 'Remote',
            'description': 'Description.',
            'password1': 'password',
            'password2': 'different',
        }

        response = self.client.post(reverse('companies:register'), data)

        self.assertIn('password2', response.context['form'].errors)
        self.assertIn('password1', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_company_login_redirects_and_rejects_students(self):
        response = self.client.post(
            reverse('companies:login'),
            {'username': self.user.username, 'password': 'StrongRecruiter123!'},
        )
        self.assertRedirects(response, reverse('companies:dashboard'))

        self.client.post(reverse('companies:logout'))
        student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        response = self.client.post(
            reverse('companies:login'),
            {'username': student.username, 'password': 'StrongStudent123!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'company accounts only')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_company_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('companies:logout'))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse('companies:logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_company_dashboard_is_protected_and_uses_real_statistics(self):
        response = self.client.get(reverse('companies:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('companies:login')}?next={reverse('companies:dashboard')}",
        )

        student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        self.client.force_login(student)
        response = self.client.get(reverse('companies:dashboard'))
        self.assertRedirects(response, reverse('home'))

        applicant = StudentProfile.objects.create(
            user=student,
            full_name='Sample Applicant',
        )
        Application.objects.create(
            student=applicant,
            internship=self.internship,
        )
        another_internship = Internship.objects.create(
            company=self.company,
            title='QA Intern',
            description='Help test software.',
            location='Remote',
            duration='3 months',
            deadline='2030-02-01',
            status=Internship.Status.OPEN,
        )
        Application.objects.create(
            student=applicant,
            internship=another_internship,
            status=Application.Status.SHORTLISTED,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('companies:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_internships'], 2)
        self.assertEqual(response.context['active_internships'], 2)
        self.assertEqual(response.context['total_applicants'], 1)
        self.assertEqual(response.context['pending_applications'], 1)
        self.assertEqual(response.context['shortlisted_candidates'], 1)
        self.assertContains(response, 'Sample Applicant')

    def test_company_profile_can_be_updated_and_invalid_logo_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('companies:profile_edit'),
            {
                'company_name': 'Updated Company',
                'contact_person': 'Jordan Recruiter',
                'phone': '+1 555 999 0000',
                'email': 'updated@example.com',
                'website': 'https://updated.example.com',
                'location': 'Boston',
                'description': 'Updated description.',
            },
        )

        self.assertRedirects(response, reverse('companies:profile'))
        self.company.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.company.company_name, 'Updated Company')
        self.assertEqual(self.company.description, 'Updated description.')
        self.assertEqual(self.user.email, 'updated@example.com')

        response = self.client.post(
            reverse('companies:profile_edit'),
            {
                'company_name': self.company.company_name,
                'contact_person': self.company.contact_person,
                'phone': self.company.phone,
                'email': self.user.email,
                'website': self.company.website,
                'location': self.company.location,
                'description': self.company.description,
                'logo': SimpleUploadedFile(
                    'logo.png',
                    b'not a real image',
                    content_type='image/png',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('logo', response.context['form'].errors)

    def test_company_can_create_edit_and_delete_its_internship(self):
        self.client.force_login(self.user)
        data = {
            'title': 'Data Intern',
            'description': 'Analyze data.',
            'location': 'Remote',
            'stipend': '1200.00',
            'duration': '4 months',
            'deadline': '2030-06-01',
            'status': Internship.Status.DRAFT,
            'required_skills': [],
        }
        response = self.client.post(
            reverse('companies:internship_create'),
            data,
        )
        self.assertRedirects(response, reverse('companies:internship_list'))
        internship = Internship.objects.get(title='Data Intern')
        self.assertEqual(internship.company, self.company)

        data['title'] = 'Data Science Intern'
        data['status'] = Internship.Status.OPEN
        response = self.client.post(
            reverse('companies:internship_edit', args=[internship.pk]),
            data,
        )
        self.assertRedirects(response, reverse('companies:internship_list'))
        internship.refresh_from_db()
        self.assertEqual(internship.title, 'Data Science Intern')
        self.assertEqual(internship.status, Internship.Status.OPEN)

        response = self.client.post(
            reverse('companies:internship_delete', args=[internship.pk]),
        )
        self.assertRedirects(response, reverse('companies:internship_list'))
        self.assertFalse(Internship.objects.filter(pk=internship.pk).exists())

    def test_internship_with_applications_cannot_be_deleted(self):
        student_user = User.objects.create_user(
            username='protectedapplicant',
            email='protected@example.com',
            password='StrongProtected123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Protected Applicant',
        )
        Application.objects.create(
            student=student,
            internship=self.internship,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('companies:internship_delete', args=[self.internship.pk]),
            follow=True,
        )

        self.assertEqual(
            response.redirect_chain,
            [(reverse('companies:internship_list'), 302)],
        )
        self.assertTrue(
            Internship.objects.filter(pk=self.internship.pk).exists(),
        )
        self.assertContains(response, 'cannot be deleted')

    def test_company_cannot_manage_another_company_posting_or_applicant(self):
        other_user = User.objects.create_user(
            username='othercompany',
            email='other@example.com',
            password='StrongOther123!',
            role=User.Role.COMPANY,
        )
        other_company = CompanyProfile.objects.create(
            user=other_user,
            company_name='Other Company',
        )
        other_internship = Internship.objects.create(
            company=other_company,
            title='Other Internship',
            description='A different role.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
        )
        student_user = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='StrongApplicant123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Private Applicant',
        )
        application = Application.objects.create(
            student=student,
            internship=other_internship,
        )
        self.client.force_login(self.user)

        protected_urls = [
            reverse('companies:internship_edit', args=[other_internship.pk]),
            reverse('companies:internship_delete', args=[other_internship.pk]),
            reverse('companies:internship_applicants', args=[other_internship.pk]),
            reverse('companies:application_detail', args=[application.pk]),
            reverse('companies:application_resume', args=[application.pk]),
        ]
        for url in protected_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

        response = self.client.post(
            reverse('companies:application_status_update', args=[application.pk]),
            {'status': Application.Status.SHORTLISTED},
        )
        self.assertEqual(response.status_code, 404)
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.PENDING)

    def test_company_can_review_applicants_and_update_status(self):
        student_user = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='StrongCandidate123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Taylor Candidate',
        )
        application = Application.objects.create(
            student=student,
            internship=self.internship,
            cover_letter='I would love to join the team.',
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('companies:internship_applicants', args=[self.internship.pk]),
        )
        self.assertContains(response, 'Taylor Candidate')

        response = self.client.get(
            reverse('companies:application_detail', args=[application.pk]),
        )
        self.assertContains(response, 'I would love to join the team.')

        response = self.client.post(
            reverse('companies:application_status_update', args=[application.pk]),
            {'status': Application.Status.SHORTLISTED},
        )
        self.assertRedirects(
            response,
            reverse('companies:application_detail', args=[application.pk]),
        )
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.SHORTLISTED)
        self.assertEqual(
            list(
                application.status_history.values_list('status', flat=True),
            ),
            [Application.Status.PENDING, Application.Status.SHORTLISTED],
        )
        self.assertEqual(
            Notification.objects.filter(user=student_user).count(),
            1,
        )

        for status in (
            Application.Status.REVIEWING,
            Application.Status.INTERVIEWING,
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
        ):
            response = self.client.post(
                reverse(
                    'companies:application_status_update',
                    args=[application.pk],
                ),
                {'status': status},
            )
            self.assertRedirects(
                response,
                reverse('companies:application_detail', args=[application.pk]),
            )

        messages = list(
            Notification.objects.filter(user=student_user).values_list(
                'message',
                flat=True,
            ),
        )
        self.assertEqual(len(messages), 5)
        self.assertTrue(any('Interviewing' in message for message in messages))
        self.assertTrue(any('Accepted' in message for message in messages))
        self.assertTrue(any('Rejected' in message for message in messages))

    def test_company_can_download_its_applicants_resume(self):
        student_user = User.objects.create_user(
            username='resumeapplicant',
            email='resume@example.com',
            password='StrongResume123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Resume Applicant',
        )
        application = Application.objects.create(
            student=student,
            internship=self.internship,
        )
        self.client.force_login(self.user)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                student.resume.save(
                    'candidate-resume.pdf',
                    SimpleUploadedFile(
                        'candidate-resume.pdf',
                        b'%PDF-1.4\n%%EOF',
                        content_type='application/pdf',
                    ),
                    save=True,
                )
                response = self.client.get(
                    reverse('companies:application_resume', args=[application.pk]),
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/pdf')
                self.assertIn('attachment', response['Content-Disposition'])
                self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4\n%%EOF')

        self.client.force_login(student_user)
        response = self.client.get(
            reverse('companies:application_resume', args=[application.pk]),
        )
        self.assertRedirects(response, reverse('home'))

    def test_company_applicants_are_searchable_filterable_and_paginated(self):
        applicants = []
        for index in range(26):
            user = User.objects.create_user(
                username=f'listedcandidate{index}',
                email=f'listedcandidate{index}@example.com',
                password='StrongCandidate123!',
                role=User.Role.STUDENT,
            )
            student = StudentProfile.objects.create(
                user=user,
                full_name=f'Listed Candidate {index}',
            )
            applicants.append(
                Application.objects.create(
                    student=student,
                    internship=self.internship,
                ),
            )
        self.client.force_login(self.user)
        url = reverse(
            'companies:internship_applicants',
            args=[self.internship.pk],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page'].paginator.count, 26)
        self.assertEqual(len(response.context['applications']), 25)

        response = self.client.get(url, {'page': 2})
        self.assertEqual(len(response.context['applications']), 1)

        response = self.client.get(
            url,
            {
                'q': applicants[0].student.full_name,
                'status': Application.Status.PENDING,
            },
        )
        self.assertEqual(response.context['page'].paginator.count, 1)
        self.assertContains(response, applicants[0].student.full_name)
        self.assertNotContains(response, applicants[1].student.full_name)

    def test_company_can_schedule_update_and_student_can_view_interview(self):
        student_user = User.objects.create_user(
            username='interviewcandidate',
            email='interviewcandidate@example.com',
            password='StrongInterview123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Interview Candidate',
        )
        application = Application.objects.create(
            student=student,
            internship=self.internship,
            status=Application.Status.SHORTLISTED,
        )
        detail_url = reverse(
            'companies:application_detail',
            args=[application.pk],
        )
        schedule_url = reverse(
            'companies:interview_schedule',
            args=[application.pk],
        )
        future_time = timezone.localtime(
            timezone.now() + timedelta(days=2),
        ).strftime('%Y-%m-%dT%H:%M')
        self.client.force_login(self.user)

        response = self.client.post(
            schedule_url,
            {
                'scheduled_at': future_time,
                'mode': Interview.Mode.ONLINE,
                'meeting_link': 'https://meet.example.com/interview',
                'location': '',
                'instructions': 'Bring a portfolio example.',
            },
        )

        self.assertRedirects(response, detail_url)
        interview = Interview.objects.get(application=application)
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.INTERVIEWING)
        self.assertEqual(
            ApplicationStatusHistory.objects.filter(
                application=application,
                status=Application.Status.INTERVIEWING,
            ).count(),
            1,
        )
        self.assertEqual(Notification.objects.filter(user=student_user).count(), 2)

        updated_time = timezone.localtime(
            timezone.now() + timedelta(days=4),
        ).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(
            schedule_url,
            {
                'scheduled_at': updated_time,
                'mode': Interview.Mode.OFFLINE,
                'meeting_link': '',
                'location': 'Building A, Room 2',
                'instructions': 'Ask for the recruiting team.',
            },
        )
        self.assertRedirects(response, detail_url)
        interview.refresh_from_db()
        self.assertEqual(interview.mode, Interview.Mode.OFFLINE)
        self.assertEqual(interview.location, 'Building A, Room 2')
        self.assertEqual(Notification.objects.filter(user=student_user).count(), 3)

        response = self.client.get(reverse('companies:dashboard'))
        self.assertContains(response, 'Upcoming interviews')
        self.assertContains(response, 'Interview Candidate')

        self.client.force_login(student_user)
        response = self.client.get(reverse('dashboard:student_dashboard'))
        self.assertContains(response, 'Interview scheduled')
        self.assertContains(response, 'Building A, Room 2')
        self.assertContains(response, 'Ask for the recruiting team.')

    def test_interview_requires_future_time_and_mode_specific_details(self):
        student_user = User.objects.create_user(
            username='invalidinterviewcandidate',
            email='invalidinterviewcandidate@example.com',
            password='StrongInterview123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Invalid Interview Candidate',
        )
        application = Application.objects.create(
            student=student,
            internship=self.internship,
            status=Application.Status.SHORTLISTED,
        )
        schedule_url = reverse(
            'companies:interview_schedule',
            args=[application.pk],
        )
        self.client.force_login(self.user)

        response = self.client.post(
            schedule_url,
            {
                'scheduled_at': timezone.localtime(
                    timezone.now() - timedelta(days=1),
                ).strftime('%Y-%m-%dT%H:%M'),
                'mode': Interview.Mode.ONLINE,
                'meeting_link': '',
                'location': '',
                'instructions': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose a future date and time')
        self.assertContains(response, 'Enter the online meeting link')
        self.assertFalse(Interview.objects.filter(application=application).exists())
        self.assertEqual(Notification.objects.filter(user=student_user).count(), 0)

    def test_students_cannot_schedule_interviews_and_recruiters_cannot_access_other_company(self):
        student_user = User.objects.create_user(
            username='permissioncandidate',
            email='permissioncandidate@example.com',
            password='StrongPermission123!',
            role=User.Role.STUDENT,
        )
        student = StudentProfile.objects.create(
            user=student_user,
            full_name='Permission Candidate',
        )
        application = Application.objects.create(
            student=student,
            internship=self.internship,
            status=Application.Status.SHORTLISTED,
        )
        schedule_url = reverse(
            'companies:interview_schedule',
            args=[application.pk],
        )
        payload = {
            'scheduled_at': timezone.localtime(
                timezone.now() + timedelta(days=2),
            ).strftime('%Y-%m-%dT%H:%M'),
            'mode': Interview.Mode.ONLINE,
            'meeting_link': 'https://meet.example.com/interview',
            'location': '',
            'instructions': '',
        }

        self.client.force_login(student_user)
        response = self.client.post(schedule_url, payload)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Interview.objects.filter(application=application).exists())

        self.client.force_login(self.user)
        other_user = User.objects.create_user(
            username='interviewothercompany',
            email='interviewothercompany@example.com',
            password='StrongOther123!',
            role=User.Role.COMPANY,
        )
        other_company = CompanyProfile.objects.create(
            user=other_user,
            company_name='Interview Other Company',
        )
        other_internship = Internship.objects.create(
            company=other_company,
            title='Private Interview Role',
            description='Another company role.',
            location='Remote',
            duration='3 months',
            deadline='2030-01-01',
            status=Internship.Status.OPEN,
        )
        other_application = Application.objects.create(
            student=student,
            internship=other_internship,
            status=Application.Status.SHORTLISTED,
        )
        response = self.client.post(
            reverse(
                'companies:interview_schedule',
                args=[other_application.pk],
            ),
            payload,
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Interview.objects.filter(application=other_application).exists(),
        )

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Skill, StudentProfile
from .validators import validate_pdf_upload


class StudentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongPass123!',
            role=User.Role.STUDENT,
        )

    def test_password_is_hashed_and_student_profile_is_one_to_one(self):
        self.assertNotEqual(self.user.password, 'StrongPass123!')
        self.assertTrue(self.user.check_password('StrongPass123!'))

        profile = StudentProfile.objects.create(
            user=self.user,
            full_name='Sample Student',
        )
        self.assertEqual(self.user.student_profile, profile)

    def test_skill_many_to_many_relationship(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            full_name='Sample Student',
        )
        skill = Skill.objects.create(name='Python')

        profile.skills.add(skill)

        self.assertIn(skill, profile.skills.all())
        self.assertIn(profile, skill.students.all())

    def test_profile_requires_student_role(self):
        company_user = User.objects.create_user(
            username='company',
            email='company@example.com',
            password='StrongPass123!',
            role=User.Role.COMPANY,
        )
        profile = StudentProfile(
            user=company_user,
            full_name='Wrong Role',
        )

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_resume_validator_rejects_non_pdf_content(self):
        upload = SimpleUploadedFile(
            'resume.pdf',
            b'not a PDF',
            content_type='application/pdf',
        )

        with self.assertRaises(ValidationError):
            validate_pdf_upload(upload)


class StudentProfileAccessTests(TestCase):
    def test_company_cannot_create_or_edit_a_student_profile(self):
        company_user = User.objects.create_user(
            username='profilecompany',
            email='profilecompany@example.com',
            password='StrongCompany123!',
            role=User.Role.COMPANY,
        )
        self.client.force_login(company_user)

        response = self.client.get(reverse('students:profile'))

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(StudentProfile.objects.filter(user=company_user).exists())

    def test_upload_storage_error_is_logged_and_reported_safely(self):
        student_user = User.objects.create_user(
            username='uploadstudent',
            email='uploadstudent@example.com',
            password='StrongStudent123!',
            role=User.Role.STUDENT,
        )
        self.client.force_login(student_user)
        with patch(
            'students.views.StudentProfileForm.save',
            side_effect=OSError('storage unavailable'),
        ):
            response = self.client.post(
                reverse('students:profile'),
                {'full_name': 'Sample Student'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'could not save your uploaded file')

from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from config.validators import validate_image_upload

from .validators import validate_pdf_upload


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='student_profile',
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s().-]{7,20}$',
                message='Enter a valid phone number.',
            ),
        ],
    )
    college = models.CharField(max_length=200, blank=True)
    degree = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    graduation_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    profile_image = models.ImageField(
        upload_to='students/profile_images/',
        blank=True,
        validators=[validate_image_upload],
    )
    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        validators=[validate_pdf_upload],
    )
    skills = models.ManyToManyField(
        Skill,
        through='StudentSkill',
        related_name='students',
        blank=True,
    )

    class Meta:
        ordering = ['full_name']

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != self.user.Role.STUDENT:
            raise ValidationError(
                {'user': 'A student profile requires a student account.'}
            )
        if (
            self.graduation_year
            and self.graduation_year > date.today().year + 10
        ):
            raise ValidationError(
                {'graduation_year': 'Graduation year is too far in the future.'}
            )

    def __str__(self):
        return self.full_name


class StudentSkill(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='student_skills',
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='student_skills',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'skill'],
                name='uniq_student_skill',
            ),
        ]
        ordering = ['skill__name']

    def __str__(self):
        return f'{self.student}: {self.skill}'

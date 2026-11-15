from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from config.validators import validate_image_upload


class CompanyProfile(models.Model):
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='company_profile',
    )
    company_name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=200, blank=True)
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
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(
        upload_to='companies/logos/',
        blank=True,
        validators=[validate_image_upload],
    )

    class Meta:
        ordering = ['company_name']

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != self.user.Role.COMPANY:
            raise ValidationError(
                {'user': 'A company profile requires a company account.'}
            )

    def __str__(self):
        return self.company_name

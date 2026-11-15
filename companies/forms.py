from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from applications.models import Application, Interview
from internships.models import Internship

from .models import CompanyProfile

User = get_user_model()


class CompanyRegistrationForm(forms.Form):
    company_name = forms.CharField(max_length=200)
    email = forms.EmailField(label='Official email')
    username = forms.CharField(
        max_length=150,
        validators=User._meta.get_field('username').validators,
    )
    contact_person = forms.CharField(max_length=200, label='Contact person name')
    phone = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s().-]{7,20}$',
                message='Enter a valid phone number.',
            ),
        ],
    )
    website = forms.URLField()
    location = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea)
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label='Password',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm password',
    )

    def clean_company_name(self):
        company_name = self.cleaned_data['company_name'].strip()
        if CompanyProfile.objects.filter(company_name__iexact=company_name).exists():
            raise forms.ValidationError('A company with this name already exists.')
        return company_name

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        if password1:
            user = User(
                username=cleaned_data.get('username', ''),
                email=cleaned_data.get('email', ''),
            )
            try:
                validate_password(password1, user=user)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned_data

    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                role=User.Role.COMPANY,
            )
            CompanyProfile.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                contact_person=self.cleaned_data['contact_person'],
                phone=self.cleaned_data['phone'],
                website=self.cleaned_data['website'],
                location=self.cleaned_data['location'],
                description=self.cleaned_data['description'],
            )
        return user


class CompanyProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Official email')

    class Meta:
        model = CompanyProfile
        fields = [
            'company_name',
            'contact_person',
            'phone',
            'email',
            'website',
            'location',
            'description',
            'logo',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.user_id,
        ).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        company = super().save(commit=False)
        if commit:
            with transaction.atomic():
                company.save()
                company.user.email = self.cleaned_data['email']
                company.user.save(update_fields=['email'])
                self.save_m2m()
        return company

    def clean_logo(self):
        upload = self.cleaned_data.get('logo')
        if not upload or getattr(upload, '_committed', False):
            return upload

        position = upload.tell()
        try:
            upload.seek(0)
            with Image.open(upload) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise forms.ValidationError('Upload a valid image file.') from None
        finally:
            upload.seek(position)
        return upload


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = [
            'title',
            'description',
            'required_skills',
            'location',
            'stipend',
            'duration',
            'deadline',
            'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'required_skills': forms.CheckboxSelectMultiple,
        }


class ApplicationStatusForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[
            (Application.Status.PENDING, 'Pending'),
            (Application.Status.REVIEWING, 'Reviewing'),
            (Application.Status.SHORTLISTED, 'Shortlisted'),
            (Application.Status.INTERVIEWING, 'Interviewing'),
            (Application.Status.REJECTED, 'Rejected'),
            (Application.Status.ACCEPTED, 'Accepted'),
        ]
    )

    class Meta:
        model = Application
        fields = ['status']


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            'scheduled_at',
            'mode',
            'meeting_link',
            'location',
            'instructions',
        ]
        widgets = {
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data['scheduled_at']
        if scheduled_at <= timezone.now():
            raise forms.ValidationError('Choose a future date and time.')
        return scheduled_at

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        meeting_link = cleaned_data.get('meeting_link')
        location = cleaned_data.get('location')

        if mode == Interview.Mode.ONLINE and not meeting_link:
            self.add_error('meeting_link', 'Enter the online meeting link.')
        elif mode == Interview.Mode.OFFLINE and not location:
            self.add_error('location', 'Enter the interview location.')
        return cleaned_data

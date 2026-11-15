from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from students.models import StudentProfile

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200, label='Full name')
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label='Password',
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm password',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password1', 'password2']

    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        user = User(
            username=self.cleaned_data.get('username', ''),
            email=self.cleaned_data.get('email', ''),
        )
        validate_password(password1, user=user)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        StudentProfile.objects.update_or_create(
            user=user,
            defaults={'full_name': self.cleaned_data['full_name']},
        )
        return user

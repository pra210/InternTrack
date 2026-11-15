from django import forms

from .models import Skill, StudentProfile


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'full_name',
            'phone',
            'college',
            'degree',
            'department',
            'graduation_year',
            'profile_image',
            'resume',
            'skills',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Jane Doe'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'college': forms.TextInput(attrs={'placeholder': 'Your college or university'}),
            'degree': forms.TextInput(attrs={'placeholder': 'B.Tech / B.E. / B.Sc.'}),
            'department': forms.TextInput(attrs={'placeholder': 'Computer Science'}),
            'graduation_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
        }

    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

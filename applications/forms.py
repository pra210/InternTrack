from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(
                attrs={
                    'rows': 7,
                    'placeholder': 'Introduce yourself and tell the hiring team why this opportunity interests you.',
                }
            ),
        }

    def clean_cover_letter(self):
        cover_letter = self.cleaned_data['cover_letter'].strip()
        if len(cover_letter) < 20:
            raise forms.ValidationError(
                'Please write at least 20 characters about your interest in this role.'
            )
        return cover_letter

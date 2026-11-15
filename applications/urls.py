from django.urls import path

from .views import apply_to_internship

app_name = 'applications'

urlpatterns = [
    path(
        'internships/<int:internship_id>/apply/',
        apply_to_internship,
        name='apply',
    ),
]

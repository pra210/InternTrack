from django.urls import path

from .views import mark_notification_read, student_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('', student_dashboard, name='student_dashboard'),
    path(
        'notifications/<int:pk>/read/',
        mark_notification_read,
        name='mark_notification_read',
    ),
]

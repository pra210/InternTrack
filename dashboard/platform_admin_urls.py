from django.urls import path

from . import platform_admin

app_name = 'platform_admin'

urlpatterns = [
    path('login/', platform_admin.platform_admin_login, name='login'),
    path('logout/', platform_admin.platform_admin_logout, name='logout'),
    path('', platform_admin.platform_dashboard, name='dashboard'),
    path('students/', platform_admin.student_management, name='students'),
    path('companies/', platform_admin.company_management, name='companies'),
    path('internships/', platform_admin.internship_management, name='internships'),
    path(
        'internships/<int:pk>/delete/',
        platform_admin.internship_delete,
        name='internship_delete',
    ),
    path(
        'internships/<int:pk>/<str:action>/',
        platform_admin.internship_status_update,
        name='internship_status_update',
    ),
    path('applications/', platform_admin.application_monitoring, name='applications'),
]

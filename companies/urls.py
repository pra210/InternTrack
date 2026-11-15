from django.urls import path

from . import views

app_name = 'companies'

urlpatterns = [
    path('register/', views.company_register, name='register'),
    path('login/', views.company_login, name='login'),
    path('logout/', views.company_logout, name='logout'),
    path('dashboard/', views.company_dashboard, name='dashboard'),
    path('profile/', views.company_profile, name='profile'),
    path('profile/edit/', views.company_profile_edit, name='profile_edit'),
    path('profile/logo/', views.company_logo, name='logo'),
    path('internships/', views.internship_list, name='internship_list'),
    path('internships/create/', views.internship_create, name='internship_create'),
    path('internships/<int:pk>/edit/', views.internship_edit, name='internship_edit'),
    path(
        'internships/<int:pk>/delete/',
        views.internship_delete,
        name='internship_delete',
    ),
    path(
        'internships/<int:pk>/applicants/',
        views.internship_applicants,
        name='internship_applicants',
    ),
    path(
        'applications/<int:pk>/',
        views.application_detail,
        name='application_detail',
    ),
    path(
        'applications/<int:pk>/status/',
        views.application_status_update,
        name='application_status_update',
    ),
    path(
        'applications/<int:pk>/interview/',
        views.interview_schedule,
        name='interview_schedule',
    ),
    path(
        'applications/<int:pk>/resume/',
        views.application_resume,
        name='application_resume',
    ),
]

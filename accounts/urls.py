from django.urls import path

from .views import login_view, logout_view, register_student

app_name = 'accounts'

urlpatterns = [
    path('register/', register_student, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]

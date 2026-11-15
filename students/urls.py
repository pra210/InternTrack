from django.urls import path

from .views import profile_view

app_name = 'students'

urlpatterns = [
    path('profile/', profile_view, name='profile'),
]

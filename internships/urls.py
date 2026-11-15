from django.urls import path

from .views import internship_detail

app_name = 'internships'

urlpatterns = [
    path('<int:pk>/', internship_detail, name='detail'),
]

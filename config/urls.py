"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from dashboard.views import health_check, home
from config import views as error_views

handler403 = error_views.permission_denied
handler404 = error_views.page_not_found
handler500 = error_views.server_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('students/', include(('students.urls', 'students'), namespace='students')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path(
        'platform-admin/',
        include(
            ('dashboard.platform_admin_urls', 'platform_admin'),
            namespace='platform_admin',
        ),
    ),
    path('companies/', include(('companies.urls', 'companies'), namespace='companies')),
    path(
        'internships/',
        include(('internships.urls', 'internships'), namespace='internships'),
    ),
    path(
        'applications/',
        include(('applications.urls', 'applications'), namespace='applications'),
    ),
    path('', home, name='home'),
    path('health/', health_check, name='health-check'),
]

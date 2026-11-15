from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'location')
    search_fields = ('company_name', 'user__username', 'location')

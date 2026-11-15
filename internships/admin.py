from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Internship


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'deadline', 'stipend')
    list_filter = ('status', 'deadline')
    search_fields = ('title', 'company__company_name', 'location')
    filter_horizontal = ('required_skills',)

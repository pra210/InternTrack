from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'internship', 'status', 'applied_date')
    list_filter = ('status', 'applied_date')
    search_fields = (
        'student__full_name',
        'student__user__username',
        'internship__title',
    )
    list_select_related = ('student', 'internship')
    readonly_fields = ('applied_date',)

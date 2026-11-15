from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Skill, StudentProfile, StudentSkill


class StudentSkillInline(admin.TabularInline):
    model = StudentSkill
    extra = 0


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'college', 'graduation_year')
    search_fields = ('full_name', 'user__username', 'college')
    inlines = (StudentSkillInline,)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ('student', 'skill')
    list_select_related = ('student', 'skill')

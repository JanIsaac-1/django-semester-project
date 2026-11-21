from django.contrib import admin
from .models import Application, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'location', 'posted_by', 'created_at')
    list_filter = ('job_type', 'created_at')
    search_fields = ('title', 'company', 'location')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job__title', 'applicant__username')

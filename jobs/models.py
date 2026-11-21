from django.contrib.auth.models import User
from django.db import models


class Job(models.Model):
    """Represents a job or internship listing posted by a user."""

    JOB_TYPES = [
        ('Internship', 'Internship'),
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='Internship')
    description = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company}"


class Application(models.Model):
    """Represents a user's application to a specific job listing."""

    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Reviewed', 'Reviewed'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"

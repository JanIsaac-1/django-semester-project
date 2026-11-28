from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from jobs.models import Job


SAMPLE_JOBS = [
    {
        'title': 'Junior Python / Django Developer Intern',
        'company': 'TechPulse Solutions',
        'location': 'Nairobi, Kenya (Hybrid)',
        'job_type': 'Internship',
        'description': 'Work alongside backend developers building REST APIs and data pipelines using Django and PostgreSQL.',
    },
    {
        'title': 'Frontend Web Developer',
        'company': 'Creative Cloud Studios',
        'location': 'Remote',
        'job_type': 'Full-time',
        'description': 'Build accessible, responsive web interfaces and integrate RESTful APIs in an agile product team.',
    },
    {
        'title': 'API Integration Specialist',
        'company': 'FinPay Africa',
        'location': 'Nairobi, Kenya',
        'job_type': 'Part-time',
        'description': 'Design, test, and document reliable payment gateway API integrations for campus merchants.',
    },
    {
        'title': 'QA & Software Testing Intern',
        'company': 'Savanna Systems',
        'location': 'Mombasa, Kenya (Hybrid)',
        'job_type': 'Internship',
        'description': 'Write automated test suites, verify API responses, and collaborate with engineers on release quality.',
    },
    {
        'title': 'Cloud & DevOps Apprentice',
        'company': 'Stratus Technologies',
        'location': 'Remote',
        'job_type': 'Internship',
        'description': 'Assist with CI/CD pipelines, container deployments, and monitoring for web applications.',
    },
    {
        'title': 'Technical Support Analyst',
        'company': 'CampusLink Networks',
        'location': 'Nairobi, Kenya',
        'job_type': 'Part-time',
        'description': 'Support student portal users, troubleshoot API webhook logs, and maintain technical documentation.',
    },
    {
        'title': 'Backend Engineer (Graduate Role)',
        'company': 'MobiServe Labs',
        'location': 'Nairobi, Kenya',
        'job_type': 'Full-time',
        'description': 'Develop scalable backend services in Python/Django and mentor incoming engineering interns.',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with a demo employer account and sample job listings.'

    def handle(self, *args, **options):
        employer, created = User.objects.get_or_create(
            username='demo_employer',
            defaults={'email': 'employer@example.com'},
        )
        if created:
            employer.set_password('DemoPass123!')
            employer.save()
            self.stdout.write(self.style.SUCCESS('Created demo user: demo_employer (password: DemoPass123!)'))

        created_count = 0
        for item in SAMPLE_JOBS:
            _, job_created = Job.objects.get_or_create(
                title=item['title'],
                company=item['company'],
                defaults={
                    'location': item['location'],
                    'job_type': item['job_type'],
                    'description': item['description'],
                    'posted_by': employer,
                },
            )
            if job_created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Seed complete: {created_count} new job(s) added.'))

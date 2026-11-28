from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Job


SAMPLE_JOBS = [
    {
        'title': 'Junior Python / Django Developer Intern',
        'company': 'TechPulse Solutions',
        'location': 'Nairobi, Kenya',
        'job_type': 'Internship',
        'work_mode': 'Hybrid',
        'salary': 'KSh 30,000 / month',
        'deadline_days': 30,
        'description': 'Work alongside backend developers building REST APIs and data pipelines using Django and PostgreSQL.',
        'requirements': 'Python basics and familiarity with Django\nUnderstanding of HTML, CSS, and Git\nStrong problem-solving skills',
    },
    {
        'title': 'Frontend Web Developer',
        'company': 'Creative Cloud Studios',
        'location': 'Remote',
        'job_type': 'Full-time',
        'work_mode': 'Remote',
        'salary': 'KSh 85,000 / month',
        'deadline_days': 45,
        'description': 'Build accessible, responsive web interfaces and integrate RESTful APIs in an agile product team.',
        'requirements': 'Proficiency in HTML5, CSS3, and modern JavaScript\nExperience consuming JSON REST APIs\nPortfolio of web projects',
    },
    {
        'title': 'API Integration Specialist',
        'company': 'FinPay Africa',
        'location': 'Nairobi, Kenya',
        'job_type': 'Part-time',
        'work_mode': 'On-site',
        'salary': 'KSh 45,000 / month',
        'deadline_days': 25,
        'description': 'Design, test, and document reliable payment gateway API integrations for campus merchants.',
        'requirements': 'Understanding of HTTP, REST, and JSON payloads\nExperience testing endpoints with Postman or curl',
    },
    {
        'title': 'QA & Software Testing Intern',
        'company': 'Savanna Systems',
        'location': 'Mombasa, Kenya',
        'job_type': 'Internship',
        'work_mode': 'Hybrid',
        'salary': 'KSh 25,000 / month',
        'deadline_days': 35,
        'description': 'Write automated test suites, verify API responses, and collaborate with engineers on release quality.',
        'requirements': 'Attention to detail and analytical mindset\nBasic Python unit testing knowledge',
    },
    {
        'title': 'Cloud & DevOps Apprentice',
        'company': 'Stratus Technologies',
        'location': 'Remote',
        'job_type': 'Internship',
        'work_mode': 'Remote',
        'salary': 'KSh 35,000 / month',
        'deadline_days': 40,
        'description': 'Assist with CI/CD pipelines, container deployments, and monitoring for web applications.',
        'requirements': 'Linux command-line familiarity\nInterest in GitHub Actions and Docker',
    },
    {
        'title': 'Technical Support Analyst',
        'company': 'CampusLink Networks',
        'location': 'Nairobi, Kenya',
        'job_type': 'Part-time',
        'work_mode': 'On-site',
        'salary': 'KSh 28,000 / month',
        'deadline_days': 20,
        'description': 'Support student portal users, troubleshoot API webhook logs, and maintain technical documentation.',
        'requirements': 'Clear written and verbal communication\nBasic SQL and web troubleshooting skills',
    },
    {
        'title': 'Backend Engineer (Graduate Role)',
        'company': 'MobiServe Labs',
        'location': 'Nairobi, Kenya',
        'job_type': 'Full-time',
        'work_mode': 'Hybrid',
        'salary': 'KSh 110,000 / month',
        'deadline_days': 60,
        'description': 'Develop scalable backend services in Python/Django and mentor incoming engineering interns.',
        'requirements': 'BSc in Computer Science or related field\n1+ year building Django web services',
    },
]


class Command(BaseCommand):
    help = 'Seed or update sample job listings and demo employer account.'

    def handle(self, *args, **options):
        employer, created = User.objects.get_or_create(
            username='demo_employer',
            defaults={
                'email': 'employer@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            employer.set_password('DemoPass123!')
            employer.save()
            self.stdout.write(self.style.SUCCESS('Created demo admin user: demo_employer (password: DemoPass123!)'))
        elif not employer.is_staff or not employer.is_superuser:
            employer.is_staff = True
            employer.is_superuser = True
            employer.save(update_fields=['is_staff', 'is_superuser'])
            self.stdout.write(self.style.SUCCESS('Updated demo_employer with admin permissions.'))

        today = timezone.localdate()
        created_count = 0
        updated_count = 0

        for item in SAMPLE_JOBS:
            deadline = today + timedelta(days=item['deadline_days'])
            job, job_created = Job.objects.get_or_create(
                title=item['title'],
                company=item['company'],
                defaults={
                    'location': item['location'],
                    'job_type': item['job_type'],
                    'work_mode': item['work_mode'],
                    'salary': item['salary'],
                    'application_deadline': deadline,
                    'description': item['description'],
                    'requirements': item['requirements'],
                    'posted_by': employer,
                },
            )
            if job_created:
                created_count += 1
            else:
                changed = False
                for field, value in (
                    ('location', item['location']),
                    ('job_type', item['job_type']),
                    ('work_mode', item['work_mode']),
                    ('salary', item['salary']),
                    ('description', item['description']),
                    ('requirements', item['requirements']),
                ):
                    if getattr(job, field) != value:
                        setattr(job, field, value)
                        changed = True
                if not job.application_deadline:
                    job.application_deadline = deadline
                    changed = True
                if changed:
                    job.save()
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Seed complete: {created_count} added, {updated_count} updated.')
        )

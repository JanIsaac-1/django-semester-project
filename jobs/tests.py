from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .forms import ApplicationForm, JobForm
from .models import Application, Job


class JobBoardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(username='employer1', password='StrongPassword123!')
        self.applicant = User.objects.create_user(username='student1', password='StrongPassword123!')
        self.job = Job.objects.create(
            title='Junior Python / Django Developer Intern',
            company='TechPulse Solutions',
            location='Nairobi, Kenya (Hybrid)',
            job_type='Internship',
            description='Work alongside backend developers building REST APIs using Django.',
            posted_by=self.employer,
        )

    def test_home_page_renders_project_template(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Campus Career & Internship Hub')

    def test_job_list_renders_database_jobs(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        self.assertContains(response, 'Available Internships and Job Openings')
        self.assertContains(response, 'Junior Python / Django Developer Intern')

    def test_job_detail_view(self):
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertContains(response, 'TechPulse Solutions')

    def test_authentication_required_for_protected_views(self):
        for url in [
            reverse('job_create'),
            reverse('apply_job', args=[self.job.pk]),
            reverse('my_applications'),
        ]:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_user_registration_and_login(self):
        # Missing email should fail validation
        invalid_res = self.client.post(reverse('register'), {
            'username': 'newstudent',
            'password1': 'UniquePassword999!',
            'password2': 'UniquePassword999!',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstudent').exists())

        # Valid registration with email
        response = self.client.post(reverse('register'), {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password1': 'UniquePassword999!',
            'password2': 'UniquePassword999!',
        })
        self.assertRedirects(response, reverse('job_list'))
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.email, 'newstudent@example.com')

        # Duplicate email should fail validation
        self.client.logout()
        dup_email_res = self.client.post(reverse('register'), {
            'username': 'anotherstudent',
            'email': 'newstudent@example.com',
            'password1': 'UniquePassword999!',
            'password2': 'UniquePassword999!',
        })
        self.assertEqual(dup_email_res.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotherstudent').exists())

    def test_login_and_logout(self):
        login_res = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'StrongPassword123!',
        })
        self.assertRedirects(login_res, reverse('job_list'))

        logout_res = self.client.post(reverse('logout'))
        self.assertRedirects(logout_res, reverse('home'))

    def test_job_form_and_creation_view(self):
        form = JobForm(data={
            'title': 'API Integration Specialist',
            'company': 'FinPay Africa',
            'location': 'Nairobi, Kenya',
            'job_type': 'Part-time',
            'description': 'Design and test scalable API endpoints.',
        })
        self.assertTrue(form.is_valid())

        self.client.login(username='employer1', password='StrongPassword123!')
        response = self.client.post(reverse('job_create'), {
            'title': 'API Integration Specialist',
            'company': 'FinPay Africa',
            'location': 'Nairobi, Kenya',
            'job_type': 'Part-time',
            'description': 'Design and test scalable API endpoints.',
        })
        created_job = Job.objects.get(title='API Integration Specialist')
        self.assertEqual(created_job.posted_by, self.employer)
        self.assertRedirects(response, reverse('job_detail', args=[created_job.pk]))

    def test_apply_job_form_and_duplicate_prevention(self):
        form = ApplicationForm(data={'cover_letter': 'Excited to contribute to the backend team.'})
        self.assertTrue(form.is_valid())

        self.client.login(username='student1', password='StrongPassword123!')
        response = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Excited to contribute to the backend team.',
        })
        self.assertRedirects(response, reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(Application.objects.filter(job=self.job, applicant=self.applicant).count(), 1)

        # Duplicate application should not create a second record
        dup_res = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Applying again.',
        })
        self.assertRedirects(dup_res, reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(Application.objects.filter(job=self.job, applicant=self.applicant).count(), 1)

        # Check my_applications view
        apps_res = self.client.get(reverse('my_applications'))
        self.assertEqual(apps_res.status_code, 200)
        self.assertContains(apps_res, self.job.title)
        self.assertContains(apps_res, 'Applied')

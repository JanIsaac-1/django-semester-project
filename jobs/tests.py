from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from .forms import ApplicationForm, ApplicationStatusForm, JobForm
from .models import Application, Job


class JobBoardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(
            username='employer1',
            email='employer1@example.com',
            password='StrongPassword123!',
        )
        self.applicant = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='StrongPassword123!',
        )
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

    def test_job_list_search_filter_and_pagination(self):
        for i in range(6):
            Job.objects.create(
                title=f'Frontend Role {i}',
                company='Studio X',
                location='Remote',
                job_type='Full-time',
                description='Build web UI components.',
                posted_by=self.employer,
            )

        # Page 1 has 6 items, Page 2 has 1 item
        page1 = self.client.get(reverse('job_list'))
        self.assertEqual(len(page1.context['jobs']), 6)
        page2 = self.client.get(reverse('job_list'), {'page': 2})
        self.assertEqual(len(page2.context['jobs']), 1)

        # Keyword search + type filter
        filtered = self.client.get(reverse('job_list'), {'q': 'TechPulse', 'job_type': 'Internship'})
        self.assertEqual(len(filtered.context['jobs']), 1)
        self.assertContains(filtered, 'Junior Python / Django Developer Intern')

        no_match = self.client.get(reverse('job_list'), {'q': 'TechPulse', 'job_type': 'Full-time'})
        self.assertEqual(len(no_match.context['jobs']), 0)
        self.assertContains(no_match, 'No matching job listings found.')

    def test_job_detail_view(self):
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_detail.html')
        self.assertContains(response, 'TechPulse Solutions')

    def test_authentication_required_for_protected_views(self):
        for url in [
            reverse('job_create'),
            reverse('job_update', args=[self.job.pk]),
            reverse('job_delete', args=[self.job.pk]),
            reverse('job_applicants', args=[self.job.pk]),
            reverse('my_posted_jobs'),
            reverse('apply_job', args=[self.job.pk]),
            reverse('my_applications'),
        ]:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_user_registration_and_login(self):
        invalid_res = self.client.post(reverse('register'), {
            'username': 'newstudent',
            'password1': 'UniquePassword999!',
            'password2': 'UniquePassword999!',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstudent').exists())

        response = self.client.post(reverse('register'), {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password1': 'UniquePassword999!',
            'password2': 'UniquePassword999!',
        })
        self.assertRedirects(response, reverse('job_list'))
        user = User.objects.get(username='newstudent')
        self.assertEqual(user.email, 'newstudent@example.com')

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

    def test_job_edit_and_delete_permissions(self):
        # Non-owner gets 403 Forbidden
        self.client.login(username='student1', password='StrongPassword123!')
        self.assertEqual(self.client.get(reverse('job_update', args=[self.job.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('job_delete', args=[self.job.pk])).status_code, 403)

        # Owner can edit
        self.client.login(username='employer1', password='StrongPassword123!')
        edit_res = self.client.post(reverse('job_update', args=[self.job.pk]), {
            'title': 'Updated Django Intern',
            'company': 'TechPulse Solutions',
            'location': 'Remote',
            'job_type': 'Internship',
            'description': 'Updated description.',
        })
        self.assertRedirects(edit_res, reverse('job_detail', args=[self.job.pk]))
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Updated Django Intern')

        # Owner can confirm and delete
        confirm_res = self.client.get(reverse('job_delete', args=[self.job.pk]))
        self.assertEqual(confirm_res.status_code, 200)
        del_res = self.client.post(reverse('job_delete', args=[self.job.pk]))
        self.assertRedirects(del_res, reverse('my_posted_jobs'))
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

    def test_owner_cannot_apply_to_own_job(self):
        self.client.login(username='employer1', password='StrongPassword123!')
        detail_res = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertContains(detail_res, 'Edit Job')
        self.assertNotContains(detail_res, 'Submit Application')

        apply_res = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Applying to own job.',
        })
        self.assertRedirects(apply_res, reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(Application.objects.count(), 0)

    def test_apply_withdraw_and_owner_status_management(self):
        form = ApplicationForm(data={'cover_letter': 'Excited to contribute to the backend team.'})
        self.assertTrue(form.is_valid())

        # Student applies
        self.client.login(username='student1', password='StrongPassword123!')
        response = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Excited to contribute to the backend team.',
        })
        self.assertRedirects(response, reverse('job_detail', args=[self.job.pk]))
        application = Application.objects.get(job=self.job, applicant=self.applicant)

        # Duplicate application blocked
        dup_res = self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Applying again.',
        })
        self.assertRedirects(dup_res, reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(Application.objects.filter(job=self.job, applicant=self.applicant).count(), 1)

        # Non-owner cannot manage applicants
        self.assertEqual(self.client.get(reverse('job_applicants', args=[self.job.pk])).status_code, 403)

        # Check my_applications view
        apps_res = self.client.get(reverse('my_applications'))
        self.assertEqual(apps_res.status_code, 200)
        self.assertContains(apps_res, self.job.title)
        self.assertContains(apps_res, 'Applied')

        # Employer views my_posted_jobs and updates applicant status
        self.client.login(username='employer1', password='StrongPassword123!')
        posted_res = self.client.get(reverse('my_posted_jobs'))
        self.assertContains(posted_res, '1 Applicant')

        status_form = ApplicationStatusForm(data={'status': 'Accepted'})
        self.assertTrue(status_form.is_valid())
        update_res = self.client.post(reverse('job_applicants', args=[self.job.pk]), {
            'application_id': application.pk,
            'status': 'Accepted',
        })
        self.assertRedirects(update_res, reverse('job_applicants', args=[self.job.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, 'Accepted')

        # Accepted application cannot be withdrawn; Applied application can
        self.client.login(username='student1', password='StrongPassword123!')
        blocked_withdraw = self.client.post(reverse('withdraw_application', args=[application.pk]))
        self.assertRedirects(blocked_withdraw, reverse('my_applications'))
        self.assertTrue(Application.objects.filter(pk=application.pk).exists())

        application.status = 'Applied'
        application.save()
        ok_withdraw = self.client.post(reverse('withdraw_application', args=[application.pk]))
        self.assertRedirects(ok_withdraw, reverse('my_applications'))
        self.assertFalse(Application.objects.filter(pk=application.pk).exists())

    def test_json_api_endpoints(self):
        list_res = self.client.get(reverse('api_job_list'))
        self.assertEqual(list_res.status_code, 200)
        payload = list_res.json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['results'][0]['title'], self.job.title)

        detail_res = self.client.get(reverse('api_job_detail', args=[self.job.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()['company'], 'TechPulse Solutions')

        missing_res = self.client.get(reverse('api_job_detail', args=[9999]))
        self.assertEqual(missing_res.status_code, 404)

    def test_seed_jobs_command_is_idempotent(self):
        call_command('seed_jobs')
        count_after_first = Job.objects.count()
        self.assertEqual(count_after_first, 7)
        call_command('seed_jobs')
        self.assertEqual(Job.objects.count(), count_after_first)

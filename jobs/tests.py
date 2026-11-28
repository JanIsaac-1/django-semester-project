import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
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
        self.assertContains(response, self.job.title)
        self.assertEqual(response.context['total_jobs'], 1)
        self.assertEqual(response.context['internship_count'], 1)

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

        mode_match = self.client.get(reverse('job_list'), {'work_mode': 'On-site'})
        self.assertGreaterEqual(len(mode_match.context['jobs']), 1)
        remote_none = self.client.get(reverse('job_list'), {'work_mode': 'Remote'})
        self.assertEqual(len(remote_none.context['jobs']), 0)

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
        login_page = self.client.get(reverse('login'))
        self.assertContains(login_page, 'Username or Email')

        # Login with username
        login_res = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'StrongPassword123!',
        })
        self.assertRedirects(login_res, reverse('job_list'))

        logout_res = self.client.post(reverse('logout'))
        self.assertRedirects(logout_res, reverse('home'))

        # Login with email (case-insensitive)
        email_login_res = self.client.post(reverse('login'), {
            'username': 'STUDENT1@EXAMPLE.COM',
            'password': 'StrongPassword123!',
        })
        self.assertRedirects(email_login_res, reverse('job_list'))

        # Wrong password with valid email should fail
        self.client.post(reverse('logout'))
        bad_login = self.client.post(reverse('login'), {
            'username': 'student1@example.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(bad_login.status_code, 200)

    def test_job_form_and_creation_view(self):
        form = JobForm(data={
            'title': 'API Integration Specialist',
            'company': 'FinPay Africa',
            'location': 'Nairobi, Kenya',
            'job_type': 'Part-time',
            'work_mode': 'Hybrid',
            'salary': 'KSh 45,000 / month',
            'application_deadline': '2026-12-31',
            'description': 'Design and test scalable API endpoints.',
            'requirements': 'REST API experience',
        })
        self.assertTrue(form.is_valid())

        self.client.login(username='employer1', password='StrongPassword123!')
        response = self.client.post(reverse('job_create'), {
            'title': 'API Integration Specialist',
            'company': 'FinPay Africa',
            'location': 'Nairobi, Kenya',
            'job_type': 'Part-time',
            'work_mode': 'Hybrid',
            'salary': 'KSh 45,000 / month',
            'application_deadline': '2026-12-31',
            'description': 'Design and test scalable API endpoints.',
            'requirements': 'REST API experience',
        })
        created_job = Job.objects.get(title='API Integration Specialist')
        self.assertEqual(created_job.posted_by, self.employer)
        self.assertEqual(created_job.work_mode, 'Hybrid')
        self.assertEqual(created_job.salary, 'KSh 45,000 / month')
        self.assertRedirects(response, reverse('job_detail', args=[created_job.pk]))

        detail_res = self.client.get(reverse('job_detail', args=[created_job.pk]))
        self.assertContains(detail_res, 'KSh 45,000 / month')
        self.assertContains(detail_res, 'REST API experience')

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

    def test_application_cv_upload_and_validation(self):
        with tempfile.TemporaryDirectory() as media_dir:
            with override_settings(MEDIA_ROOT=media_dir):
                invalid_file = SimpleUploadedFile('script.exe', b'binary', content_type='application/octet-stream')
                invalid_form = ApplicationForm(
                    data={'cover_letter': 'Test cover letter'},
                    files={'cv': invalid_file},
                )
                self.assertFalse(invalid_form.is_valid())
                self.assertIn('cv', invalid_form.errors)

                pdf_file = SimpleUploadedFile('my_cv.pdf', b'%PDF-1.4 test resume', content_type='application/pdf')
                self.client.login(username='student1', password='StrongPassword123!')
                response = self.client.post(reverse('apply_job', args=[self.job.pk]), {
                    'cover_letter': 'Attached my CV for review.',
                    'cv': pdf_file,
                })
                self.assertRedirects(response, reverse('job_detail', args=[self.job.pk]))

                application = Application.objects.get(job=self.job, applicant=self.applicant)
                self.assertTrue(application.cv.name.startswith('cvs/my_cv'))

                detail_res = self.client.get(reverse('job_detail', args=[self.job.pk]))
                self.assertContains(detail_res, 'View Uploaded CV')

                self.client.login(username='employer1', password='StrongPassword123!')
                applicants_res = self.client.get(reverse('job_applicants', args=[self.job.pk]))
                self.assertContains(applicants_res, 'View / Download CV')

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

    def test_toggle_job_status_close_and_reopen(self):
        # Non-owner gets 403
        self.client.login(username='student1', password='StrongPassword123!')
        self.assertEqual(self.client.post(reverse('toggle_job_status', args=[self.job.pk])).status_code, 403)

        # Owner closes the job
        self.client.login(username='employer1', password='StrongPassword123!')
        close_res = self.client.post(reverse('toggle_job_status', args=[self.job.pk]))
        self.assertRedirects(close_res, reverse('my_posted_jobs'))
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_active)

        # Closed job hidden from public listing, home counts, and API list
        self.assertEqual(len(self.client.get(reverse('job_list')).context['jobs']), 0)
        self.assertEqual(self.client.get(reverse('home')).context['total_jobs'], 0)
        self.assertEqual(self.client.get(reverse('api_job_list')).json()['count'], 0)

        # Applicants cannot apply to a closed job
        self.client.login(username='student1', password='StrongPassword123!')
        apply_res = self.client.post(reverse('apply_job', args=[self.job.pk]), {'cover_letter': 'Trying to apply'})
        self.assertRedirects(apply_res, reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(Application.objects.count(), 0)

        # Owner reopens the job
        self.client.login(username='employer1', password='StrongPassword123!')
        self.client.post(reverse('toggle_job_status', args=[self.job.pk]))
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_active)
        self.assertEqual(len(self.client.get(reverse('job_list')).context['jobs']), 1)

    def test_profile_update_and_password_change(self):
        self.assertRedirects(
            self.client.get(reverse('profile')),
            f"{reverse('login')}?next={reverse('profile')}",
        )

        self.client.login(username='student1', password='StrongPassword123!')
        get_res = self.client.get(reverse('profile'))
        self.assertEqual(get_res.status_code, 200)
        self.assertTemplateUsed(get_res, 'registration/profile.html')

        # Duplicate email taken by employer1 should be rejected
        dup_res = self.client.post(reverse('profile'), {
            'username': 'student1',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'employer1@example.com',
        })
        self.assertEqual(dup_res.status_code, 200)

        # Valid update
        ok_res = self.client.post(reverse('profile'), {
            'username': 'student1',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@example.com',
        })
        self.assertRedirects(ok_res, reverse('profile'))
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.first_name, 'Jane')
        self.assertEqual(self.applicant.email, 'jane.doe@example.com')

        # Password change flow
        pw_res = self.client.post(reverse('password_change'), {
            'old_password': 'StrongPassword123!',
            'new_password1': 'NewStrongPass456!',
            'new_password2': 'NewStrongPass456!',
        })
        self.assertRedirects(pw_res, reverse('password_change_done'))

    def test_custom_error_templates_exist_and_render_on_404(self):
        with override_settings(DEBUG=False):
            res = self.client.get('/non-existent-route/')
            self.assertEqual(res.status_code, 404)
            self.assertTemplateUsed(res, '404.html')

    def test_admin_dashboard_access_and_actions(self):
        # Anonymous user redirects to login
        self.assertRedirects(
            self.client.get(reverse('admin_dashboard')),
            f"{reverse('login')}?next={reverse('admin_dashboard')}",
        )

        # Non-staff user gets 403 Forbidden and does not see Admin Dashboard header button
        self.client.login(username='student1', password='StrongPassword123!')
        self.assertNotContains(self.client.get(reverse('home')), 'Admin Dashboard')
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 403)

        # Staff user logs in and lands directly on Admin Dashboard
        application = Application.objects.create(
            job=self.job,
            applicant=self.applicant,
            cover_letter='Admin dashboard test application.',
        )
        User.objects.create_user(
            username='site_admin',
            email='admin@example.com',
            password='AdminPassword123!',
            is_staff=True,
            is_superuser=True,
        )
        self.client.logout()
        login_res = self.client.post(reverse('login'), {
            'username': 'site_admin',
            'password': 'AdminPassword123!',
        })
        self.assertRedirects(login_res, reverse('admin_dashboard'))

        dash_res = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertTemplateUsed(dash_res, 'jobs/admin_dashboard.html')
        self.assertContains(dash_res, 'Admin Dashboard')
        self.assertContains(dash_res, self.job.title)
        self.assertContains(dash_res, 'student1')

        # Update application status from dashboard
        status_res = self.client.post(reverse('admin_dashboard'), {
            'application_id': application.pk,
            'status': 'Reviewed',
        })
        self.assertRedirects(status_res, reverse('admin_dashboard'))
        application.refresh_from_db()
        self.assertEqual(application.status, 'Reviewed')

        # Admin can toggle another user's job status and redirect back to dashboard
        toggle_res = self.client.post(reverse('toggle_job_status', args=[self.job.pk]), {
            'next': reverse('admin_dashboard'),
        })
        self.assertRedirects(toggle_res, reverse('admin_dashboard'))
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_active)

    def test_seed_jobs_command_is_idempotent(self):
        call_command('seed_jobs')
        demo_admin = User.objects.get(username='demo_employer')
        self.assertTrue(demo_admin.is_staff)
        self.assertTrue(demo_admin.is_superuser)
        count_after_first = Job.objects.count()
        self.assertEqual(count_after_first, 7)
        call_command('seed_jobs')
        self.assertEqual(Job.objects.count(), count_after_first)

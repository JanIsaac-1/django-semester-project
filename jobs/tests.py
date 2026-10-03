from django.test import TestCase, Client
from django.urls import reverse

class JobViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_renders_project_template(self):
        """Verify project-level template renders with status 200."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Campus Career & Internship Hub')

    def test_job_list_renders_app_template(self):
        """Verify app-level template renders with status 200."""
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        self.assertContains(response, 'Available Internships and Job Openings')
        self.assertContains(response, 'Junior Python / Django Developer Intern')

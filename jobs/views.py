from django.shortcuts import render

def home(request):
    """View rendering project-level template (home.html)."""
    return render(request, 'home.html')

def job_list(request):
    """View rendering app-level template (jobs/job_list.html)."""
    sample_jobs = [
        {
            'title': 'Junior Python / Django Developer Intern',
            'company': 'TechPulse Solutions',
            'location': 'Nairobi, Kenya (Hybrid)',
            'job_type': 'Internship',
            'description': 'Work alongside backend developers building REST APIs and data pipelines using Django.'
        },
        {
            'title': 'Frontend Web Developer',
            'company': 'Creative Cloud Studios',
            'location': 'Remote',
            'job_type': 'Full-time',
            'description': 'Develop modern web interfaces and consume RESTful web services in an agile environment.'
        },
        {
            'title': 'API Integration Specialist',
            'company': 'FinPay Africa',
            'location': 'Nairobi, Kenya',
            'job_type': 'Part-time',
            'description': 'Design, test, and document scalable API endpoints for payment gateway integration.'
        }
    ]
    return render(request, 'jobs/job_list.html', {'jobs': sample_jobs})

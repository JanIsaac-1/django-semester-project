from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationForm, JobForm, UserRegisterForm
from .models import Application, Job


def home(request):
    """Render the project-level home page."""
    return render(request, 'home.html')


def job_list(request):
    """List all jobs stored in the database."""
    jobs = Job.objects.select_related('posted_by').all()
    return render(request, 'jobs/job_list.html', {'jobs': jobs})


def job_detail(request, pk):
    """Show job details and application status/form."""
    job = get_object_or_404(Job.objects.select_related('posted_by'), pk=pk)
    existing_application = None
    form = None

    if request.user.is_authenticated:
        existing_application = Application.objects.filter(job=job, applicant=request.user).first()
        if not existing_application:
            form = ApplicationForm()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'existing_application': existing_application,
        'form': form,
    })


@login_required
def job_create(request):
    """Allow an authenticated user to post a new job listing."""
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, 'Job listing posted successfully.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm()

    return render(request, 'jobs/job_form.html', {'form': form})


@login_required
def apply_job(request, pk):
    """Allow an authenticated user to apply for a specific job."""
    job = get_object_or_404(Job, pk=pk)
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('job_detail', pk=job.pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = ApplicationForm()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'existing_application': None,
        'form': form,
    })


@login_required
def my_applications(request):
    """List applications submitted by the current user."""
    applications = Application.objects.select_related('job').filter(applicant=request.user)
    return render(request, 'jobs/my_applications.html', {'applications': applications})


def register(request):
    """Register a new user account and log them in."""
    if request.user.is_authenticated:
        return redirect('job_list')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('job_list')
    else:
        form = UserRegisterForm()

    return render(request, 'registration/register.html', {'form': form})

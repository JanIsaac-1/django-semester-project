from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ApplicationForm, ApplicationStatusForm, JobForm, UserRegisterForm
from .models import Application, Job


def _get_owned_job(request, pk):
    """Return a Job or raise PermissionDenied if the current user is not the poster."""
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by != request.user:
        raise PermissionDenied('You do not have permission to manage this job listing.')
    return job


def _filter_jobs(request):
    """Filter Job queryset by keyword 'q' and 'job_type' query parameters."""
    query = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    jobs = Job.objects.select_related('posted_by').all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(location__icontains=query)
            | Q(description__icontains=query)
        )

    valid_types = {choice[0] for choice in Job.JOB_TYPES}
    if job_type in valid_types:
        jobs = jobs.filter(job_type=job_type)
    else:
        job_type = ''

    return jobs, query, job_type


def _serialize_job(job):
    """Convert a Job model instance into a JSON-serializable dictionary."""
    return {
        'id': job.pk,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'job_type': job.job_type,
        'description': job.description,
        'posted_by': job.posted_by.username,
        'created_at': job.created_at.isoformat(),
    }


def home(request):
    """Render the project-level home page."""
    return render(request, 'home.html')


def job_list(request):
    """List jobs with optional search, job_type filter, and pagination."""
    jobs_qs, query, selected_type = _filter_jobs(request)
    paginator = Paginator(jobs_qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'jobs/job_list.html', {
        'jobs': page_obj,
        'page_obj': page_obj,
        'query': query,
        'selected_type': selected_type,
        'job_types': Job.JOB_TYPES,
    })


def job_detail(request, pk):
    """Show job details and either owner controls or the application form."""
    job = get_object_or_404(Job.objects.select_related('posted_by'), pk=pk)
    is_owner = request.user.is_authenticated and job.posted_by == request.user
    existing_application = None
    form = None

    if request.user.is_authenticated and not is_owner:
        existing_application = Application.objects.filter(job=job, applicant=request.user).first()
        if not existing_application:
            form = ApplicationForm()

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'is_owner': is_owner,
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

    return render(request, 'jobs/job_form.html', {'form': form, 'job': None})


@login_required
def job_update(request, pk):
    """Allow the job owner to edit their job listing."""
    job = _get_owned_job(request, pk)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job listing updated successfully.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'job': job})


@login_required
def job_delete(request, pk):
    """Allow the job owner to delete their job listing after confirmation."""
    job = _get_owned_job(request, pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job listing deleted.')
        return redirect('my_posted_jobs')

    return render(request, 'jobs/job_confirm_delete.html', {'job': job})


@login_required
def my_posted_jobs(request):
    """List jobs posted by the current user with applicant counts."""
    jobs = (
        Job.objects.filter(posted_by=request.user)
        .annotate(application_count=Count('applications'))
    )
    return render(request, 'jobs/my_posted_jobs.html', {'jobs': jobs})


@login_required
def job_applicants(request, pk):
    """Allow the job owner to view applicants and update application statuses."""
    job = _get_owned_job(request, pk)

    if request.method == 'POST':
        application = get_object_or_404(Application, pk=request.POST.get('application_id'), job=job)
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Updated {application.applicant.username}'s status to {application.status}.",
            )
            return redirect('job_applicants', pk=job.pk)

    applications = job.applications.select_related('applicant').all()
    application_rows = [
        (application, ApplicationStatusForm(instance=application))
        for application in applications
    ]
    return render(request, 'jobs/job_applicants.html', {
        'job': job,
        'application_rows': application_rows,
    })


@login_required
def apply_job(request, pk):
    """Allow an authenticated user to apply for another user's job."""
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by == request.user:
        messages.warning(request, 'You cannot apply to your own job listing.')
        return redirect('job_detail', pk=job.pk)

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
        'is_owner': False,
        'existing_application': None,
        'form': form,
    })


@login_required
@require_POST
def withdraw_application(request, pk):
    """Allow the applicant to withdraw a pending application."""
    application = get_object_or_404(Application, pk=pk)
    if application.applicant != request.user:
        raise PermissionDenied('You cannot withdraw someone else\'s application.')

    if application.status != 'Applied':
        messages.warning(request, 'Only pending applications can be withdrawn.')
        return redirect('my_applications')

    application.delete()
    messages.success(request, 'Application withdrawn.')
    return redirect('my_applications')


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


@require_GET
def api_job_list(request):
    """Return a JSON list of job listings with optional 'q' and 'job_type' filters."""
    jobs_qs, _, _ = _filter_jobs(request)
    results = [_serialize_job(job) for job in jobs_qs]
    return JsonResponse({'count': len(results), 'results': results})


@require_GET
def api_job_detail(request, pk):
    """Return JSON details for a single job listing."""
    job = Job.objects.select_related('posted_by').filter(pk=pk).first()
    if not job:
        return JsonResponse({'error': 'Job not found.'}, status=404)
    return JsonResponse(_serialize_job(job))

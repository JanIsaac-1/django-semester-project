from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .forms import ApplicationForm, ApplicationStatusForm, JobForm, UserLoginForm, UserProfileForm, UserRegisterForm
from .models import Application, Job


def _get_owned_job(request, pk):
    """Return a Job or raise PermissionDenied if user is neither the poster nor staff."""
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by != request.user and not request.user.is_staff:
        raise PermissionDenied('You do not have permission to manage this job listing.')
    return job


def _filter_jobs(request):
    """Filter active Job queryset by keyword 'q', 'job_type', and 'work_mode' query params."""
    query = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    jobs = Job.objects.select_related('posted_by').filter(is_active=True)

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(location__icontains=query)
            | Q(work_mode__icontains=query)
            | Q(description__icontains=query)
            | Q(requirements__icontains=query)
        )

    valid_types = {choice[0] for choice in Job.JOB_TYPES}
    if job_type in valid_types:
        jobs = jobs.filter(job_type=job_type)
    else:
        job_type = ''

    valid_modes = {choice[0] for choice in Job.WORK_MODES}
    if work_mode in valid_modes:
        jobs = jobs.filter(work_mode=work_mode)
    else:
        work_mode = ''

    return jobs, query, job_type, work_mode


def _serialize_job(job):
    """Convert a Job model instance into a JSON-serializable dictionary."""
    return {
        'id': job.pk,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'job_type': job.job_type,
        'work_mode': job.work_mode or 'On-site',
        'salary': job.salary,
        'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
        'description': job.description,
        'requirements': job.requirements,
        'is_active': job.is_active,
        'posted_by': job.posted_by.username,
        'created_at': job.created_at.isoformat(),
    }


def home(request):
    """Render the project-level home page with live active job counts and recent openings."""
    active_jobs = Job.objects.select_related('posted_by').filter(is_active=True)
    recent_jobs = active_jobs[:3]
    total_jobs = active_jobs.count()
    internship_count = active_jobs.filter(job_type='Internship').count()
    fulltime_count = active_jobs.filter(job_type='Full-time').count()
    parttime_count = active_jobs.filter(job_type='Part-time').count()
    return render(request, 'home.html', {
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'internship_count': internship_count,
        'fulltime_count': fulltime_count,
        'parttime_count': parttime_count,
    })


def job_list(request):
    """List jobs with optional search, job_type/work_mode filters, and pagination."""
    jobs_qs, query, selected_type, selected_mode = _filter_jobs(request)
    paginator = Paginator(jobs_qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'jobs/job_list.html', {
        'jobs': page_obj,
        'page_obj': page_obj,
        'query': query,
        'selected_type': selected_type,
        'selected_mode': selected_mode,
        'job_types': Job.JOB_TYPES,
        'work_modes': Job.WORK_MODES,
    })


def job_detail(request, pk):
    """Show job details and either owner controls or the application form."""
    job = get_object_or_404(Job.objects.select_related('posted_by'), pk=pk)
    is_owner = request.user.is_authenticated and job.posted_by == request.user
    existing_application = None
    form = None

    if request.user.is_authenticated and not is_owner:
        existing_application = Application.objects.filter(job=job, applicant=request.user).first()
        if not existing_application and job.is_active:
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
@require_POST
def toggle_job_status(request, pk):
    """Allow the job owner to close or reopen their job listing."""
    job = _get_owned_job(request, pk)
    job.is_active = not job.is_active
    job.save(update_fields=['is_active'])
    state_label = 'reopened' if job.is_active else 'closed'
    messages.success(request, f'Job listing "{job.title}" has been {state_label}.')

    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('my_posted_jobs')


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

    if not job.is_active:
        messages.warning(request, 'This job listing is closed and no longer accepting applications.')
        return redirect('job_detail', pk=job.pk)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('job_detail', pk=job.pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
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

    if application.cv:
        application.cv.delete(save=False)
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


class CustomLoginView(auth_views.LoginView):
    """Redirect staff/admin users to the Admin Dashboard after login."""

    template_name = 'registration/login.html'
    authentication_form = UserLoginForm

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        if self.request.user.is_staff:
            return reverse('admin_dashboard')
        return super().get_success_url()


@login_required
def profile(request):
    """Allow authenticated users to view and update their account details."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'registration/profile.html', {
        'form': form,
        'posted_count': request.user.posted_jobs.count(),
        'application_count': request.user.applications.count(),
    })


@login_required
def admin_dashboard(request):
    """Dedicated site-wide admin dashboard for staff and superusers."""
    if not request.user.is_staff:
        raise PermissionDenied('Only administrators can access the admin dashboard.')

    if request.method == 'POST':
        application = get_object_or_404(Application, pk=request.POST.get('application_id'))
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Updated {application.applicant.username}'s application for {application.job.title} to {application.status}.",
            )
            return redirect('admin_dashboard')

    all_jobs = Job.objects.select_related('posted_by').annotate(application_count=Count('applications'))
    recent_applications = Application.objects.select_related('job', 'applicant')[:20]
    application_rows = [
        (application, ApplicationStatusForm(instance=application))
        for application in recent_applications
    ]
    users = User.objects.annotate(
        posted_count=Count('posted_jobs', distinct=True),
        app_count=Count('applications', distinct=True),
    ).order_by('-date_joined')

    return render(request, 'jobs/admin_dashboard.html', {
        'total_users': users.count(),
        'open_jobs_count': Job.objects.filter(is_active=True).count(),
        'closed_jobs_count': Job.objects.filter(is_active=False).count(),
        'total_applications': Application.objects.count(),
        'pending_applications_count': Application.objects.filter(status='Applied').count(),
        'all_jobs': all_jobs,
        'application_rows': application_rows,
        'users': users,
    })


@require_GET
def api_job_list(request):
    """Return a JSON list of job listings with optional filters."""
    jobs_qs, _, _, _ = _filter_jobs(request)
    results = [_serialize_job(job) for job in jobs_qs]
    return JsonResponse({'count': len(results), 'results': results})


@require_GET
def api_job_detail(request, pk):
    """Return JSON details for a single job listing."""
    job = Job.objects.select_related('posted_by').filter(pk=pk).first()
    if not job:
        return JsonResponse({'error': 'Job not found.'}, status=404)
    return JsonResponse(_serialize_job(job))

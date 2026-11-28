from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_update, name='job_update'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<int:pk>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('jobs/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('my-jobs/', views.my_posted_jobs, name='my_posted_jobs'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('applications/<int:pk>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
        ),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html',
        ),
        name='password_change_done',
    ),
    path('api/jobs/', views.api_job_list, name='api_job_list'),
    path('api/jobs/<int:pk>/', views.api_job_detail, name='api_job_detail'),
]

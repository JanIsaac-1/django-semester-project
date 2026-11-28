# Campus Career & Internship Hub

A Django web application developed for **API – Application Programming for the Internet (Semester Project)**.

---

## Features

- **User Authentication**: Registration (with unique email validation), login with either **username or email**, and logout powered by Django's authentication framework.
- **Job & Internship Listings**: Browse paginated openings with keyword search (`?q=`), employment type filtering (`Internship`, `Full-time`, `Part-time`), and work mode filtering (`On-site`, `Hybrid`, `Remote`).
- **Full Employer CRUD & Applicant Management**: Post detailed job listings (including work mode, salary/stipend, application deadline, and requirements), edit, close/reopen, or delete your own listings, review applicants with downloadable CVs, and update application statuses (`Applied`, `Reviewed`, `Accepted`, `Rejected`).
- **Account Profile & Password Management**: View and edit account details (`/profile/`) and change passwords (`/password-change/`), plus custom `403` and `404` error pages.
- **Dedicated Admin Dashboard**: Staff/admin users (`demo_employer`) get an in-app Admin Dashboard (`/dashboard/`) to monitor users, manage all job listings, and review/update all applications alongside Django's built-in `/admin/`.
- **Student Applications & CV Upload**: Apply to listings with a cover letter and optional CV upload (`.pdf`, `.doc`, `.docx` up to 5 MB), track statuses on **My Applications**, and withdraw pending applications.
- **JSON API Endpoints**: Read-only JSON endpoints (`/api/jobs/` and `/api/jobs/<id>/`) supporting search and filtering.

---

## Project Structure

```text
iap-sem-project/
├── .gitignore
├── README.md
├── requirements.txt
├── manage.py
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── jobs/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── backends.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_jobs.py
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_application_cv.py
│   │   ├── 0003_job_application_deadline_job_requirements_job_salary_and_more.py
│   │   └── 0004_job_is_active.py
│   └── templates/
│       └── jobs/
│           ├── admin_dashboard.html
│           ├── job_applicants.html
│           ├── job_confirm_delete.html
│           ├── job_detail.html
│           ├── job_form.html
│           ├── job_list.html
│           ├── my_applications.html
│           └── my_posted_jobs.html
└── templates/
    ├── 403.html
    ├── 404.html
    ├── base.html
    ├── home.html
    └── registration/
        ├── login.html
        ├── password_change_done.html
        ├── password_change_form.html
        ├── profile.html
        └── register.html
```

---

## Setup & Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/JanIsaac-1/django-semester-project.git
cd django-semester-project
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. (Optional) Load sample demo data
```bash
python manage.py seed_jobs
```
This creates a demo admin/employer account (`demo_employer` / `DemoPass123!`, with access to `/dashboard/` and `/admin/`) and 7 sample job/internship listings.

### 6. Start the development server
```bash
python manage.py runserver
```
Open `http://127.0.0.1:8000/` in your browser.

---

## Key Routes

| Route | Description |
|---|---|
| `/` | Home page with quick search, category counts, and recent openings |
| `/jobs/` | Job listings (search, job type & work mode filters, pagination) |
| `/jobs/create/` | Post a new job (login required) |
| `/jobs/<id>/` | Job details, requirements, & application form with CV upload |
| `/jobs/<id>/edit/` | Edit job listing (owner only) |
| `/jobs/<id>/toggle-status/` | Close or reopen job listing (owner only) |
| `/jobs/<id>/delete/` | Delete job listing (owner only) |
| `/jobs/<id>/applicants/` | View applicants, download CVs, & update statuses (owner only) |
| `/my-jobs/` | Jobs posted by the current user |
| `/my-applications/` | Applications submitted by the current user |
| `/dashboard/` | Dedicated site-wide Admin Dashboard (staff/admin only) |
| `/profile/`, `/password-change/` | Account profile & password management |
| `/register/`, `/login/`, `/logout/` | Account registration & authentication |
| `/api/jobs/`, `/api/jobs/<id>/` | JSON API endpoints |

---

## Running Tests
```bash
python manage.py test
```

# Campus Career & Internship Hub

A Django web application developed for **API – Application Programming for the Internet (Semester Project)**.

---

## Features

- **User Authentication**: Registration (with unique email validation), login, and logout powered by Django's authentication framework.
- **Job & Internship Listings**: Browse paginated job openings with keyword search (`?q=`) and type filtering (`Internship`, `Full-time`, `Part-time`).
- **Full Employer CRUD & Applicant Management**: Post new jobs, edit or delete your own listings, review applicants, and update application statuses (`Applied`, `Reviewed`, `Accepted`, `Rejected`).
- **Student Applications**: Apply to listings with a cover letter (duplicate and self-applications prevented), track statuses on **My Applications**, and withdraw pending applications.
- **JSON API Endpoints**: Read-only JSON endpoints (`/api/jobs/` and `/api/jobs/<id>/`) supporting the same search and job-type filters.

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
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_jobs.py
│   ├── migrations/
│   │   └── 0001_initial.py
│   └── templates/
│       └── jobs/
│           ├── job_applicants.html
│           ├── job_confirm_delete.html
│           ├── job_detail.html
│           ├── job_form.html
│           ├── job_list.html
│           ├── my_applications.html
│           └── my_posted_jobs.html
└── templates/
    ├── base.html
    ├── home.html
    └── registration/
        ├── login.html
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
This creates a demo employer account (`demo_employer` / `DemoPass123!`) and 7 sample job/internship listings.

### 6. Start the development server
```bash
python manage.py runserver
```
Open `http://127.0.0.1:8000/` in your browser.

---

## Key Routes

| Route | Description |
|---|---|
| `/` | Home page |
| `/jobs/` | Job listings (search, filter, pagination) |
| `/jobs/create/` | Post a new job (login required) |
| `/jobs/<id>/` | Job details & application form |
| `/jobs/<id>/edit/` | Edit job listing (owner only) |
| `/jobs/<id>/delete/` | Delete job listing (owner only) |
| `/jobs/<id>/applicants/` | View & update applicant statuses (owner only) |
| `/my-jobs/` | Jobs posted by the current user |
| `/my-applications/` | Applications submitted by the current user |
| `/register/`, `/login/`, `/logout/` | Account registration & authentication |
| `/api/jobs/`, `/api/jobs/<id>/` | JSON API endpoints |

---

## Running Tests
```bash
python manage.py test
```

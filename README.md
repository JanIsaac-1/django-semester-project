# Campus Career & Internship Hub

A Django web application developed for **API – Application Programming for the Internet (Semester Project)**.

---

## Project Structure

```text
iap-sem-project/
├── .gitignore
├── README.md
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
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── templates/
│       └── jobs/
│           └── job_list.html      <-- App-level template
└── templates/
    ├── base.html                  <-- Project-level template
    └── home.html                  <-- Project-level template
```

---

## Setup & Running Locally

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd "iap sem project"
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Django
```bash
pip install django
```

### 4. Apply database migrations
```bash
python manage.py migrate
```

### 5. Run the development server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## Running Unit Tests
```bash
python manage.py test
```

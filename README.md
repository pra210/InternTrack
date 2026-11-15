# InternTrack – Smart Internship & Placement Management System

InternTrack is a full-stack Django application that connects students, companies, and platform administrators through a centralized internship and placement management platform. Students can discover opportunities, apply for positions, and track their progress. Companies can publish internships, review applicants, and schedule interviews, while administrators manage and monitor the platform.

> **Project status:** Local development and testing are complete. Production deployment is pending; Render is the planned platform.

## 1. Overview

Finding internships and managing applications can involve multiple platforms and disconnected communication. InternTrack brings these activities together in one organized system with role-based access and dedicated dashboards.

The platform provides separate experiences for:

- **Students:** Discover internships, manage profiles, apply for opportunities, and track application progress.
- **Companies and recruiters:** Create internship postings, review applications, update candidate statuses, and schedule interviews.
- **Platform administrators:** Manage students, companies, internships, and applications through an administrative dashboard.

## 2. Features

### 2.1 Student Portal

- Student registration and secure login.
- Student profile creation and management.
- Skills and resume management.
- Browse and search internship opportunities.
- View internship details and eligibility information.
- Apply for internships with a cover letter.
- Track application status and history.
- View interview schedules and notifications.
- Access a personalized student dashboard.

### 2.2 Company and Recruiter Portal

- Company registration and login.
- Company profile management.
- Create, update, and manage internship postings.
- View applicants for the company's internships.
- Review candidate profiles and applications.
- Update application statuses and shortlist candidates.
- Schedule interviews with date, time, mode, and meeting details.
- Access a dedicated recruiter dashboard.

### 2.3 Platform Administration

- Protected platform administrator login.
- Dashboard overview with platform statistics.
- Manage student and company records.
- Manage internship postings.
- Monitor applications.
- Role- and permission-restricted administrative access.

### 2.4 Application Tracking and Notifications

- Track application progress and status history.
- Notify students about application updates.
- Display scheduled interview details.
- Mark notifications as read.

### 2.5 Security and Access Control

- Role-based access control for students, companies, and administrators.
- Protected views and dashboard routes.
- Django authentication and session management.
- CSRF protection.
- Failed-login throttling using Django Axes.
- Environment-based secret and database configuration.
- Private handling of uploaded resumes and access-controlled downloads.

## 3. Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.14.7 |
| Web framework | Django 5.2.18 |
| Frontend | HTML5, CSS3, JavaScript |
| Database | MySQL Server 8.0 |
| Authentication and login throttling | Django authentication, Django Axes 9.0.0 |
| Database driver | mysqlclient 2.3.1 |
| Environment configuration | python-dotenv 1.2.4 |
| Static file handling | WhiteNoise 6.11.0 |
| Image processing | Pillow 13.0.0 |
| Production application server | Gunicorn 23.0.0 (Linux deployment) |
| Version control | Git and GitHub |

The listed versions reflect the current project environment and dependency configuration.

## 4. Project Architecture

```text
InternTrack/
├── accounts/       # User authentication, accounts, and notifications
├── applications/   # Internship application and interview workflows
├── companies/      # Company and recruiter functionality
├── config/         # Django project configuration and settings
├── dashboard/      # Student dashboard and platform administration
├── internships/    # Internship browsing and management
├── students/       # Student profiles and functionality
├── templates/      # HTML templates
├── static/         # Source CSS, JavaScript, and other static assets
├── staticfiles/    # Generated static files (collectstatic output)
├── media/          # Local uploads; keep private and out of Git
├── .env.example    # Example environment variable names and values
├── .gitignore      # Ignored local, generated, and private files
├── DEPLOYMENT.md   # Deployment preparation and security guidance
├── manage.py       # Django management entry point
├── README.md
└── requirements.txt
```

The local `.env` file and uploaded media are private and must not be committed. `staticfiles/` is generated during deployment preparation; edit source assets under `static/` instead.

## 5. Getting Started

These instructions describe a local Windows development setup.

### 5.1 Prerequisites

- Python 3.14.7 (the version used for the recorded verification).
- MySQL Server 8.0.
- Git.
- PowerShell and Visual Studio Code or another code editor.
- MySQL Workbench is optional.

### 5.2 Clone the Repository

```powershell
git clone https://github.com/pra210/InternTrack.git
Set-Location InternTrack
```

### 5.3 Create a Virtual Environment and Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use the `.venv` interpreter for the commands below to ensure Django and project dependencies are installed in the environment running the application.

### 5.4 Configure MySQL

If you are creating a new local database, create it in MySQL:

```sql
CREATE DATABASE interntrack_db CHARACTER SET utf8mb4;
```

Create or configure a MySQL application user with appropriate privileges. Do not use the MySQL root account for the application. If you already have a project database, do not recreate or reset it.

### 5.5 Configure Environment Variables

If `.env` does not already exist, copy the example file:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set the values for your local environment in `.env`. The settings use these variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Private Django signing key |
| `DEBUG` | Enables or disables Django debug mode |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins |
| `DB_NAME` | MySQL database name |
| `DB_USER` | MySQL application username |
| `DB_PASSWORD` | MySQL application password |
| `DB_HOST` | MySQL host |
| `DB_PORT` | MySQL port |

Optional database TLS and connection settings are documented in `.env.example` and [`DEPLOYMENT.md`](DEPLOYMENT.md). Keep `.env` private; never commit real passwords, secret keys, or other credentials.

### 5.6 Apply Migrations

Review the migration plan before applying migrations to an existing database:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
```

Applying migrations is not a database reset, but individual migrations can change the schema or data. Review the migration plan and back up an existing database before applying changes.

### 5.7 Create an Administrator and Start Django

Create an authorized Django administrator:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Start the local development server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## 6. Testing and Verification

The recorded local verification is:

- **58 automated Django tests passed.**
- **Django system check passed** with no issues reported.
- **All 10 Django Axes migrations are applied.**
- The configured MySQL database reports its project migrations as applied.

Run the test suite and system check locally:

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py showmigrations
```

## 7. Security and Deployment Considerations

- Keep secrets in environment variables; never commit `.env`.
- Keep private uploaded media out of Git and do not serve resumes from a public media URL.
- Resume downloads are routed through authenticated, company-authorized views.
- The default upload storage is local filesystem storage. A production deployment still needs durable, private media storage configured for the hosting environment.
- Production also requires a configured MySQL database, production environment variables, HTTPS, secure cookies, and static-file collection.
- Django Axes tracks failed logins by client IP. If deployed behind a reverse proxy, configure IP resolution for the trusted proxy topology.
- Review [`DEPLOYMENT.md`](DEPLOYMENT.md) for additional deployment preparation and security guidance.

**Production deployment is not complete, and the application is not claimed to be live.** Render is the planned deployment platform. Production database configuration, hosting, HTTPS, static files, and private durable media storage still need to be configured and verified.

## 8. Future Enhancements

- Email notifications for important application events.
- Advanced internship recommendations.
- Analytics and placement reports.
- Enhanced recruiter and student insights.
- Additional automated deployment and monitoring workflows.

## 9. Author

**Praveen K**  
B.Tech – Computer Science and Engineering  
GitHub: [@pra210](https://github.com/pra210)

## 10. Repository

[InternTrack – Smart Internship & Placement Management System](https://github.com/pra210/InternTrack)

If you find this project useful, consider giving the repository a star on GitHub.

*Built with Python, Django, MySQL, and a focus on secure, organized internship management.*

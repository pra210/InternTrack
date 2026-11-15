# InternTrack – Smart Internship & Placement Management System

A full-stack Django web application that connects students, companies and platform administrators through a centralized internship and placement management platform.
InternTrack helps students discover internship opportunities, apply for positions and track their application progress. Companies can publish internships, review applicants and schedule interviews, while administrators manage and monitor the platform.

Project Status: Development completed; production deployment preparation in progress.

## Overview

Finding internships and managing applications can involve multiple platforms and disconnected communication. InternTrack brings these activities together in one organized system with role-based access and dedicated dashboards.

The platform provides separate experiences for:

- Students: Discover internships, manage profiles, apply for opportunities and track application progress.
- Companies / Recruiters: Create internship postings, review applications, update candidate statuses and schedule interviews.
- Platform Administrators: Manage students, companies, internships and applications through an administrative dashboard.

## Key Features

 1. Student Portal
- Student registration and secure login.
- Student profile creation and management.
- Skills and resume management.
- Browse and search internship opportunities.
- View internship details and eligibility information.
- Apply for internships with a cover letter.
- Track application status and history.
- View interview schedules and notifications.
- Access a personalized student dashboard.

2. Company / Recruiter Portal
- Company registration and login.
- Company profile management.
- Create, update and manage internship postings.
- View applicants for published internships.
- Review candidate profiles and applications.
- Update application statuses.
- Shortlist candidates.
- Schedule interviews with date, time, mode and meeting details.
- Access a dedicated recruiter dashboard.

 3. Platform Administration
- Protected platform administrator login.
- Dashboard overview with platform statistics.
- Manage student records.
- Manage company records.
- Manage internship postings.
- Monitor and manage applications.
- Role-restricted administrative access.

 4. Application Tracking and Notifications
- Track application progress.
- Maintain application status history.
- Notify students about application updates.
- Display interview schedules.
- Manage notification read status.

5. Security and Access Control
- Role-based access control for students, companies and administrators.
- Protected views and dashboard routes.
- Django authentication and session management.
- CSRF protection.
- Login attempt throttling using Django Axes.
- Environment-based secret and database configuration.
- Private handling of uploaded resumes.
- Access-controlled resume downloads.

## Technology Stack

| Layer | Technology |
| Backend | Python, Django |
| Frontend | HTML5, CSS3, JavaScript |
| Database | MySQL 8.0 |
| Authentication | Django Authentication, Django Axes |
| Static Files | WhiteNoise |
| Image Processing | Pillow |
| Database Driver | mysqlclient |
| Version Control | Git and GitHub |
| Production Server | Gunicorn |

## Project Architecture

InternTrack/
│
├── accounts/          # User authentication and accounts
├── applications/      # Internship application workflow
├── companies/         # Company and recruiter functionality
├── config/            # Django project configuration
├── dashboard/         # Dashboards and platform administration
├── internships/       # Internship management
├── students/          # Student profiles and functionality
│
├── templates/         # HTML templates
├── static/            # CSS, JavaScript and static assets
│
├── .env.example       # Example environment configuration
├── .gitignore         # Git ignored files
├── DEPLOYMENT.md      # Deployment preparation guide
├── manage.py
└── requirements.txt

## Getting Started

Follow these steps to run InternTrack locally.

Prerequisites

Install the following:

- Python 3.12 or later compatible with the project dependencies.
- MySQL Server 8.0.
- MySQL Workbench (optional, for database management).
- Git.
- Visual Studio Code or another code editor.

1. Clone the Repository

```bash
git clone https://github.com/pra210/InternTrack.git
cd InternTrack
```

2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

4. Configure the Database

Create a MySQL database:

```sql
CREATE DATABASE interntrack_db;
```

Configure a MySQL application user with appropriate database permissions. Do not use the MySQL root account for production.

5. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a reference.

```powershell
Copy-Item .env.example .env
```

## Update the local configuration with your own values:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

Keep your `.env` file private. Never commit real credentials or secret keys to GitHub.

6. Apply Database Migrations

```bash
python manage.py migrate
```

7. Create a Platform Administrator

```bash
python manage.py createsuperuser
```

Follow the prompts to create an authorized administrator account.

8. Run the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

## Testing and Verification

The project includes automated Django tests covering application functionality, authentication, permissions and other workflows.

## Latest local verification:

- 58 automated tests passed.
- Django system check completed without issues.
- All 10 Django Axes migrations applied successfully.
- Existing MySQL database migration completed successfully.

Run the tests locally:

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

---

## Security Considerations

- Sensitive configuration is stored in environment variables.
- `.env`, virtual environments and private uploaded media are excluded from Git.
- Django Axes provides failed-login attempt tracking.
- Student, company and administrator functionality is protected by role-based access checks.
- Uploaded resumes are handled through authenticated access-controlled routes.
- Production deployment requires HTTPS, secure cookies, a production database and private durable media storage.

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment preparation and security guidance.

## Deployment Status

The project has completed local development and automated testing.

Production deployment is not yet completed. The deployment process requires configuring:

- Production environment variables and secret keys.
- A managed MySQL database with appropriate credentials and TLS.
- Hosting platform settings and HTTPS.
- Persistent private media storage for uploaded resumes.
- Static file collection and production server configuration.

The application is being prepared for deployment using Render.

## Future Enhancements

- Email notifications for important application events.
- Advanced internship recommendations.
- Analytics and placement reports.
- Enhanced recruiter and student insights.
- Additional automated deployment and monitoring workflows.

Author
Praveen K

B.Tech – Computer Science and Engineering

GitHub: [@pra210](https://github.com/pra210)

## Repository

**InternTrack – Smart Internship & Placement Management System**

[https://github.com/pra210/InternTrack](https://github.com/pra210/InternTrack)

If you find this project useful, consider giving the repository a ⭐ on GitHub.

*Built with Python, Django, MySQL and a focus on secure, organized internship management.*

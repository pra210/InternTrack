# InternTrack deployment preparation

This project is prepared for a conventional Linux deployment behind an HTTPS
reverse proxy. No deployment, database reset, or credential change is performed
by this guide. Keep production credentials in the hosting provider's secret
manager or environment settings; do not commit a `.env` file.

## 1. Configure the environment

Copy `.env.example` to `.env` for local work. For production, configure these
environment variables in the deployment platform instead:

| Variable | Production guidance |
| --- | --- |
| `SECRET_KEY` | Generate a new, private Django key. Never reuse the example value. |
| `DEBUG` | Set to `False`. |
| `ALLOWED_HOSTS` | Comma-separated hostnames only, without schemes or paths. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated full HTTPS origins, for example `https://your-domain.example`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Use a least-privilege MySQL application account. Do not use the MySQL root account. |
| `DB_SSL_CA` | Optional path to the managed MySQL server CA certificate when TLS verification is required by the provider. |
| `DB_CONN_MAX_AGE` | Persistent connection lifetime in seconds; tune for the hosting platform's connection limits. |
| `STATIC_ROOT` | Writable build/runtime directory for collected static assets. |
| `MEDIA_ROOT` | Durable, private storage location for uploads. |
| `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | Leave enabled in production. |
| `SECURE_HSTS_SECONDS` | Start at `0`; increase only after HTTPS is fully working for every served hostname. |
| `USE_X_FORWARDED_PROTO` | Enable only when a trusted reverse proxy overwrites and controls this header. |

Generate a key in a trusted local shell or deployment secret manager:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the real deployment hostnames.
Do not include wildcard hosts. Keep `DEBUG=False`; Django refuses to start
without an explicit production `ALLOWED_HOSTS` value.

## 2. Install and prepare the application

For local development on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py runserver
```

For production, build the release in the deployment environment, then run:

```sh
python -m pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

Run Gunicorn behind a TLS-terminating reverse proxy or managed HTTPS ingress.
Do not expose the Gunicorn port directly to the public internet. Tune worker
count and timeouts for the selected host and workload.

For an existing database, take a verified backup before a release, review
`python manage.py migrate --plan`, and apply only the migrations required by
that release. Login throttling uses django-axes' database-backed attempt
tracking, so its migrations must be applied before serving authenticated
requests. These migrations add Axes tables and do not reset or delete existing
InternTrack records.

## 3. Static and media storage

WhiteNoise serves compressed, manifest-hashed CSS and JavaScript from
`STATIC_ROOT`; run `collectstatic` for every release and serve the generated
directory through the Django application. Do not edit collected files directly.
The source assets remain in `static/`.

Uploads under `MEDIA_ROOT` include private resumes. Do not configure a public
web-server or object-storage URL that exposes the media directory. Resume
downloads are streamed by the authenticated company application route, which
checks that the requesting company owns the application. Company logos are
also returned through an authenticated route. Keep the media volume private,
durable, access-controlled, backed up, and encrypted at rest as appropriate.
If object storage is introduced, use private containers and short-lived,
authorized delivery rather than public object URLs.

The application currently validates resumes as PDF files no larger than 5 MB
and images no larger than 3 MB. Also enforce upload-size limits at the reverse
proxy/load balancer and review the storage provider's file-scanning policy.

## 4. Operational security

- Use HTTPS for the entire site. Keep secure session and CSRF cookies enabled.
- Failed logins are throttled by client IP: five failed attempts in a rolling
  30-minute window result in HTTP 429; a successful login clears that IP's
  failure count. If Django runs behind a reverse proxy, configure Axes IP
  resolution for the trusted proxy topology so clients cannot spoof their IP.
- Configure MySQL network access and TLS according to the provider's guidance;
  use a restricted application DB account and keep credentials out of source.
- Treat `media/` as private. Never add a public `/media/` alias for resumes.
- Configure the host to collect standard output/error logs. Application logs
  contain exception details for operators; restrict log access and retention.
- Configure monitoring, database backups, media backups, and restore testing
  separately from application releases.
- `403`, `404`, and `500` responses use generic branded pages. With `DEBUG=False`,
  public error responses do not render Django tracebacks.

## 5. Verification

```sh
python manage.py test
python manage.py check --database default
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
```

Production deployment checks depend on real hostnames, HTTPS/proxy settings,
and deployment topology. Resolve any warnings that apply to the chosen host
before publishing a release. This repository does not include provider-specific
infrastructure, a TLS certificate, production secrets, or an automated deploy
pipeline.

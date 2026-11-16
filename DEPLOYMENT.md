# InternTrack deployment preparation

Use `DJANGO_ENV=production` for a production deployment. Local development keeps
using the existing MySQL environment variables and does not require TiDB Cloud
credentials. Keep production credentials in Render environment settings or
secret files; never commit `.env` files.

## 1. Configure the environment

Copy `.env.example` to `.env` for local work. Configure the following values in
the Render service instead of uploading a local `.env` file:

| Variable | Production guidance |
| --- | --- |
| `DJANGO_ENV` | Set to `production` to enable production-only validation and security settings. |
| `SECRET_KEY` | Generate a new, private Django key. Never reuse the example value. |
| `DEBUG` | Must be `False` in production. |
| `ALLOWED_HOSTS` | Comma-separated hostnames only, without schemes or paths. Include the Render hostname. |
| `CSRF_TRUSTED_ORIGINS` | Required comma-separated HTTPS origins, such as `https://your-service.onrender.com`. |
| `DB_NAME` | TiDB database name, for example `interntrack_db`. |
| `DB_USER`, `DB_PASSWORD` | TiDB application account credentials. Use Render's protected environment settings. |
| `DB_HOST`, `DB_PORT` | TiDB Cloud connection endpoint and port from its connection instructions. Both must be explicitly set; do not use the local defaults. |
| `DB_SSL_CA` | Required filesystem path to the TiDB Cloud CA certificate file. In production, the file must exist and Django configures `ssl_mode=VERIFY_IDENTITY`. |
| `DB_CONN_MAX_AGE` | Optional persistent connection lifetime in seconds; default is 60. Tune for provider connection limits. |
| `DB_CONNECT_TIMEOUT` | Optional MySQL connection timeout in seconds; default is 10. |
| `STATIC_ROOT` | Writable build/runtime directory for collected static assets. |
| `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | Production settings require these to remain enabled. |
| `SECURE_HSTS_SECONDS` | Start at `0`; increase only after HTTPS is fully working for every served hostname. |
| `LOG_LEVEL` | Optional application logging level; defaults to `WARNING`. |

Generate a key in a trusted local shell or deployment secret manager:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the real deployment hostnames.
Do not include wildcard hosts. Production settings require explicit hosts and
CSRF origins, reject `DEBUG=True`, require the TiDB host, port, and CA file, and
verify the database certificate and hostname. The Render TLS-terminating proxy
is trusted for `X-Forwarded-Proto` only in production mode; do not expose the
application through an alternate untrusted proxy path.

## 2. Install and prepare the application

For local development on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py runserver
```

The WSGI module is `config.wsgi:application`. Configure this Render web
service's build and start commands as follows:

**Build command**

```sh
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start command**

```sh
sh start.sh
```

The startup script requires `DJANGO_ENV=production`, runs
`python manage.py migrate --noinput` against the database configured by the
production settings, and starts Gunicorn only if migrations succeed. Django
uses the configured `DB_SSL_CA` and verified TLS settings for that connection.
Render requires the web service to bind to `0.0.0.0` and provides `PORT`.

The script runs at every service start. Django applies only migrations not
already recorded as applied; the command does not create migrations, flush,
reset, fake, or delete database data. The checked-in project migrations create
or alter tables/fields, and the applications history migration adds history
rows for existing applications once. Review any future migrations for data
changes before deploying them. This startup approach is intended for the
single Render Free web instance; if the service is scaled to multiple
instances, use a single coordinated migration runner rather than having each
instance migrate concurrently.

Before changing the Render Start Command, confirm the service's environment
points to the intended TiDB database and take a backup if it contains data. If
a migration fails, the script exits without starting Gunicorn. Review the
Render deploy logs and database state before retrying; do not use `--fake`,
flush, or reset commands to bypass a failure.

Keep migrations out of the Render build command: builds prepare static files,
while the startup script performs the migration using the service's configured
production environment. Render Free does not provide Shell access, but the
Start Command can be set in the web service's dashboard to `sh start.sh`.

For a database that contains records, take a verified backup before a release
and review each migration's schema and data operations. The startup script
applies every unapplied project and django-axes migration before serving
requests. Do not mark migrations applied with `--fake` or use database reset
commands to work around an error.

## 3. Static and media storage

WhiteNoise serves compressed, manifest-hashed CSS and JavaScript from
`STATIC_ROOT`; run `collectstatic` for every release and serve the generated
directory through the Django application. Do not edit collected files directly.
The source assets remain in `static/`.

Uploads under `MEDIA_ROOT` include resumes, profile images, and company logos.
The default Django file storage writes to the local filesystem. Render Free's
service filesystem is temporary, so changing `MEDIA_ROOT` to another local
directory does not make uploads durable. Before accepting production uploads,
configure a durable private storage backend (for example, a private
object-storage bucket) and backups. Do not make a bucket or media directory
public. Resume downloads and company logos must remain behind the application's
authorization checks; if external object storage is introduced, use private
objects and authorized delivery.

The application currently validates resumes as PDF files no larger than 5 MB
and images no larger than 3 MB. Also enforce upload-size limits at the reverse
proxy/load balancer and review the storage provider's file-scanning policy.

## 4. Operational security

- Use HTTPS for the entire site. Keep secure session and CSRF cookies enabled.
- Failed logins are throttled by client IP: five failed attempts in a rolling
  30-minute window result in HTTP 429; a successful login clears that IP's
  failure count. In production, Axes uses `REMOTE_ADDR`; it does not trust
  `X-Forwarded-For`.
- Configure MySQL network access and TLS according to the provider's guidance;
  use a restricted application DB account and keep credentials out of source.
- Treat `media/` as private. Never add a public `/media/` alias for resumes.
  Render Free does not provide durable local media storage.
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

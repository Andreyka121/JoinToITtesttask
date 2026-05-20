# Event Management API

Django REST API for managing events (conferences, meetups, etc.) with user registration and authentication.

## Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.0 + Django REST Framework |
| Database | PostgreSQL 16 |
| Authentication | JWT (djangorestframework-simplejwt) |
| API Docs | Swagger / ReDoc (drf-spectacular) |
| Filtering | django-filter + DRF SearchFilter |
| Server | Gunicorn |
| Infrastructure | Docker + docker-compose |

## Quick Start

**1. Clone and configure environment:**

```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

**2. Build and run:**

```bash
docker-compose up --build
```

**3. Create a superuser (optional):**

```bash
docker-compose exec api python manage.py createsuperuser
```

The API is now available at `http://localhost:8000`

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |
| `http://localhost:8000/admin/` | Django Admin |

---

## API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/token/` | Login — returns access + refresh tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| GET | `/api/auth/me/` | Get current user profile | Yes |
| PUT/PATCH | `/api/auth/me/` | Update current user profile | Yes |

**Register example:**
```json
POST /api/auth/register/
{
  "email": "user@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Login example:**
```json
POST /api/auth/token/
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

Use the returned `access` token in all authenticated requests:
```
Authorization: Bearer <access_token>
```

---

### Events

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/events/` | List all events | No |
| POST | `/api/events/` | Create event | Yes |
| GET | `/api/events/{id}/` | Get event detail | No |
| PUT | `/api/events/{id}/` | Update event | Organizer only |
| PATCH | `/api/events/{id}/` | Partial update | Organizer only |
| DELETE | `/api/events/{id}/` | Delete event | Organizer only |
| POST | `/api/events/{id}/register/` | Register for event | Yes |
| DELETE | `/api/events/{id}/unregister/` | Unregister from event | Yes |
| GET | `/api/events/{id}/participants/` | List participants | Yes |

**Create event example:**
```json
POST /api/events/
{
  "title": "DjangoCon Ukraine 2026",
  "description": "Annual Django conference",
  "date": "2026-09-15T10:00:00Z",
  "location": "Kyiv, Ukraine"
}
```

---

### Filtering & Search

All query parameters can be combined on `GET /api/events/`:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `title` | `?title=django` | Title contains (case-insensitive) |
| `location` | `?location=kyiv` | Location contains (case-insensitive) |
| `date_from` | `?date_from=2026-06-01T00:00:00Z` | Events from this date |
| `date_to` | `?date_to=2026-12-31T23:59:59Z` | Events until this date |
| `organizer` | `?organizer=1` | Filter by organizer ID |
| `search` | `?search=python` | Full-text search in title, description, location |
| `ordering` | `?ordering=-date` | Sort by field (`-` prefix for descending) |
| `limit` | `?limit=10` | Page size |
| `offset` | `?offset=20` | Pagination offset |

---

## Email Notifications

Users receive a confirmation email upon registering for an event.

**Development** — emails are printed to the Docker console (default):
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Production** — configure real SMTP in `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

> In a production system with high traffic, email sending should be moved to an async task queue (Celery + Redis) to avoid blocking requests.

---

## Project Structure

```
.
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── src/
    ├── manage.py
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── apps/
        ├── users/          # Custom user model, JWT auth endpoints
        │   ├── models.py
        │   ├── serializers.py
        │   ├── views.py
        │   └── urls.py
        └── events/         # Events CRUD, registration, filtering
            ├── models.py
            ├── serializers.py
            ├── views.py
            ├── filters.py
            ├── permissions.py
            └── signals.py  # Email notification on registration
```

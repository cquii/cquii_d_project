# Employees API

A REST API built with Django REST Framework over the [MySQL Employees sample database](https://github.com/datacharmer/test_db). The project focuses on query performance, reusable architecture, and clean environment configuration.

## Stack

- Python / Django 6 / Django REST Framework
- MySQL (employees data) + SQLite (auth/sessions)
- `python-decouple` for environment-based configuration

## Key Design Decisions

### Smart Pagination
Automatically selects the pagination strategy based on table size:

| Table size | Class | Strategy |
|------------|-------|----------|
| ≤ 10,000 rows | `StandardPagination` | Offset-based; response includes `count` and `last_page` |
| > 10,000 rows | `HybridPagination` | Cursor-based by default; supports page jumps (see below) |

Row count is cached for 5 minutes to avoid redundant queries. Page size is configurable via `?page_size=`. An explicit `pagination_class` on a viewset overrides auto-detection.

#### HybridPagination — cursor + page-jump combined

Large tables use `HybridPagination`, which supports two mutually exclusive modes per request:

**Cursor mode** (default) — pure cursor navigation, no `OFFSET` cost:
```
GET /employees/                   → first page; next/previous are cursor URLs
GET /employees/?cursor=<token>    → navigate sequentially
```

**Page-jump mode** — `?page=<N>` jumps to any page via a single `OFFSET` query, then hands off to cursor:
```
GET /employees/?page=50           → jumps to page 50
```

After a page jump, `next` and `previous` in the response carry cursor tokens — so all subsequent navigation is cursor-based and incurs no further `OFFSET` cost.

**Priority rule:** if both `?cursor` and `?page` appear in the same request, cursor mode wins.

Response shape is consistent across both modes:
```json
{
  "count":     null,
  "last_page": null,
  "next":      "https://host/employees/?cursor=eyJwIjo...",
  "previous":  null,
  "results":   [...]
}
```
`count` and `last_page` are always `null` for cursor-based responses because computing a total count on large tables is expensive.

### N+1 Prevention with `select_related`
Viewsets declare `select_related` fields explicitly. The base viewset applies them automatically in `get_queryset()`, keeping views clean and queries efficient.

### Database Router
All `employees_app` models route to the MySQL `employees` database. Auth and session models stay on the default SQLite database. No manual `using()` calls needed anywhere.

### Reusable Base Classes
- **`BaseModelViewSet`** — configurable viewset with filtering, searching, ordering, select_related, and auto-pagination built in
- **`BaseFilterSet`** — helper methods for range and date-range filters, used across all FilterSet classes

### Settings Split
| Module | Purpose |
|--------|---------|
| `base.py` | Shared settings, reads `SECRET_KEY` from env |
| `development.py` | `DEBUG=True`, MySQL from `.env`, SQL logging to console |
| `testing.py` | In-memory SQLite, logging silenced, fast MD5 hasher |
| `production.py` | `DEBUG=False`, HTTPS enforced, HSTS, secure cookies |

## API Endpoints

All endpoints support filtering, searching, ordering, and pagination.

| Endpoint | Resource |
|----------|----------|
| `GET /employees/` | Employee records |
| `GET /departments/` | Department records |
| `GET /dept-emp/` | Employee–department assignments |
| `GET /dept-manager/` | Department manager assignments |
| `GET /salaries/` | Salary history |
| `GET /titles/` | Job title history |

Full CRUD (GET, POST, PUT, PATCH, DELETE) available on all endpoints.

### Filtering examples

```
/employees/?gender=M&hire_date__gte=1990-01-01&ordering=-hire_date
/salaries/?emp_no=10001&salary__gte=60000&salary__lte=100000
/titles/?title__icontains=engineer
/dept-emp/?dept_no=d005&from_date__gte=1995-01-01
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```ini
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=employees
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

### 3. Load the employees database

```bash
mysql -u root -p < test_db/employees.sql
```

### 4. Run migrations and start

```bash
python manage.py migrate
python manage.py runserver
```

## Running Tests

Uses in-memory SQLite — no MySQL connection required.

```bash
python manage.py test --settings=d_project.settings.testing
```

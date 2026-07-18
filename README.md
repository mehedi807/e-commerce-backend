# E-Commerce Order & Payment System

Backend API for managing products, processing orders, and handling payments through Stripe and bKash.

## Tech Stack

* **Backend**: Django 6.0, Django REST Framework
* **Database & Caching**: PostgreSQL 18 (using Psycopg 3), Redis 8 (using django-redis)
* **Payment Gateways**: Stripe (Checkout + webhooks), bKash (Sandbox API + token cache + AWS SNS webhooks)
* **Authentication**: JWT authentication via djangorestframework-simplejwt (email as identifier)
* **API Documentation**: OpenAPI 3 schema generated via drf-spectacular (Swagger UI)
* **Infrastructure**: Multi-stage Docker builds, docker-compose orchestration, GitHub Actions CI/CD

## Architecture

This project uses a services/selectors pattern. Business logic for writes goes into `services.py`, reads go into `selectors.py`. APIs are plain `APIView` classes with inline `InputSerializer` and `OutputSerializer` definitions, not model-coupled serializers or ViewSets.

All errors go through a custom exception handler in `core.exceptions` that returns a consistent `{message, extra}` format.

## Project Structure

Each business application follows a service-layer pattern separating APIs, queries (selectors), and mutations (services):

```text
├── authentication/      # User accounts and JWT management
├── products/            # Product catalog and nested category tree
├── orders/              # Checkout flow and order lifecycle management
├── payments/            # Gateways, webhooks, and provider integrations
│   └── providers/       # Stripe and bKash SDK/API adapters
├── core/                # Shared utilities, exceptions, and API schemas
├── config/              # Django settings and root URL configuration
└── docs/                # Setup and environment reference documents
```

### Feature Folder Pattern
Every feature directory (such as `products` or `orders`) is organized consistently:
* `apis.py` contains REST API endpoints, serializers, and permission checks.
* `services.py` contains write operations, database transactions, and business logic.
* `selectors.py` contains read operations, filters, database queries, and caching logic.
* `models.py` contains database table definitions.
* `tests/` contains component-level test suites.

## API Endpoints

Full request/response schemas are in Swagger at `/api/docs/`.

### Authentication (`/api/auth/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register/` | No | Register and get tokens |
| POST | `/login/` | No | Login and get tokens |
| GET | `/me/` | Yes | Current user profile |
| POST | `/token/refresh/` | No | Refresh JWT |

### Products (`/api/products/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | List products with filters (status, category, price range, search) |
| GET | `/<id>/` | No | Product detail |
| GET | `/categories/` | No | Flat category list |
| GET | `/categories/tree/` | No | Nested category tree, cached in Redis |

### Products Admin (`/api/admin/products/`, `/api/admin/categories/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/admin/products/` | Admin | Create product |
| PUT | `/api/admin/products/<id>/update/` | Admin | Update product |
| DELETE | `/api/admin/products/<id>/delete/` | Admin | Delete product |
| POST | `/api/admin/categories/` | Admin | Create category |

### Orders (`/api/orders/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | Yes | Create order |
| GET | `/list/` | Yes | List my orders |
| GET | `/<id>/` | Yes | Order detail |
| POST | `/<id>/cancel/` | Yes | Cancel pending order |

### Orders Admin (`/api/admin/orders/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Admin | List all orders |
| GET | `/<id>/` | Admin | Any order detail |
| POST | `/<id>/status/` | Admin | Update order status |

### Payments (`/api/payments/`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/initiate/` | Yes | Start payment (Stripe or bKash) |
| POST | `/bkash/execute/` | Yes | Execute bKash payment |
| POST | `/bkash/query/` | Yes | Query bKash payment status |
| GET | `/order/<id>/` | Yes | List payments for an order |
| POST | `/webhooks/stripe/` | No | Stripe webhook |
| POST | `/webhooks/bkash/` | No | bKash webhook |

### Other

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/core/health/` | No | Health check |
| GET | `/api/schema/` | No | OpenAPI schema (JSON) |
| GET | `/api/docs/` | No | Swagger UI |

## Getting Started

### Docker (recommended)

```bash
cp .env.example .env
# Fill in the values, see docs/environment_configuration.md for reference

docker compose -f docker-compose.dev.yml up
```

The dev compose also runs an ngrok tunnel for webhook testing. Details in [docs/ngrok_setup.md](docs/ngrok_setup.md).

### Local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point DATABASE_URL and REDIS_URL in .env to your local instances
python manage.py migrate
python manage.py runserver
```

## Running Tests

```bash
python manage.py test
```

## Documentation

- [Environment Configuration](docs/environment_configuration.md) for all `.env` variables
- [Ngrok Setup](docs/ngrok_setup.md) for local webhook tunnel setup

## Deployment

Pushing to `main` triggers a GitHub Actions pipeline that builds a Docker image, pushes it to GHCR, and deploys to VPS. It includes a health check with automatic rollback. See [deploy.yml](.github/workflows/deploy.yml).

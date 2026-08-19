# 🏢 Enterprise SaaS API

Production-grade multi-tenant SaaS REST API built with FastAPI, PostgreSQL, Redis, and Celery.

## 🚀 Tech Stack

- **FastAPI** — async REST API framework
- **PostgreSQL** — primary database
- **SQLAlchemy + Alembic** — ORM and migrations
- **Redis** — caching + Celery broker
- **Celery + Flower** — async task queue
- **JWT** — stateless authentication
- **Prometheus + Grafana** — metrics and monitoring
- **Docker + Docker Compose** — containerization
- **GitHub Actions** — CI/CD pipeline
- **Nginx** — reverse proxy

## 🏗️ Architecture
Client → Nginx → FastAPI (3 replicas)
↓
PostgreSQL (primary DB)
Redis (cache + broker)
Celery Worker (async tasks)
Prometheus (metrics)
Grafana (dashboards)


## ✨ Features

- ✅ Multi-tenant organization management
- ✅ Role-based access control (Owner / Admin / Member)
- ✅ Project and task management per organization
- ✅ API key generation and revocation
- ✅ Webhook system with HMAC-SHA256 signing
- ✅ Immutable audit log for compliance
- ✅ Redis caching with TTL and cache invalidation
- ✅ Async email notifications via SendGrid
- ✅ Structured JSON logging with request tracing
- ✅ Rate limiting per user/IP
- ✅ Prometheus metrics + Grafana dashboards
- ✅ GitHub Actions CI/CD pipeline
- ✅ Security headers on every response
- ✅ Global exception handlers with consistent error shape

## 📊 API Endpoints (46 total)

| Module | Endpoints |
|--------|-----------|
| Auth | 2 |
| Organizations | 4 |
| Members | 4 |
| Projects | 5 |
| Tasks | 5 |
| API Keys | 3 |
| Webhooks | 4 |
| Audit Logs | 1 |
| System | 3 |

## 🚀 Quick Start

### Local Development

```bash
# Clone repo
git clone https://github.com/sivamani151dev-cell/enterprise-saas-api
cd enterprise-saas-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your values

# Run migrations
python -m alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Docker (Full Stack)

```bash
docker-compose up --build
```

This starts:
- FastAPI on http://localhost:8000
- Swagger UI on http://localhost:8000/docs
- Flower (Celery monitor) on http://localhost:5555
- Prometheus on http://localhost:9090
- Grafana on http://localhost:3000

## 🔐 Authentication

All protected endpoints require JWT Bearer token:
Authorization: Bearer <your-token>


Get token via `POST /api/v1/auth/login`

## 🪝 Webhook System

Register a URL to receive real-time event notifications:

```json
POST /api/v1/orgs/{slug}/webhooks
{
  "url": "https://your-server.com/webhook",
  "events": ["member.invited", "task.completed"]
}
```

Every delivery is signed with HMAC-SHA256:
X-Webhook-Signature: sha256=<signature>
X-Webhook-Event: member.invited

## 📋 Audit Logs

Every action is logged immutably:

```json
GET /api/v1/orgs/{slug}/audit-logs

{
  "action": "member.invited",
  "actor_id": "uuid",
  "resource_type": "membership",
  "old_value": null,
  "new_value": {"email": "user@example.com", "role": "member"},
  "ip_address": "127.0.0.1",
  "created_at": "2026-08-19T10:30:00Z"
}
```

## 📈 Monitoring

Prometheus scrapes `/metrics` every 15 seconds.
Import `monitoring/grafana/dashboard.json` into Grafana for pre-built dashboard.

## 🧪 Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## 🔒 Security

- JWT authentication on all protected routes
- bcrypt password hashing
- HMAC-SHA256 webhook signature verification
- Rate limiting (100 req/min default)
- Security headers (XSS, clickjacking, MIME sniffing protection)
- API keys hashed before storage (never stored in plain text)
- Input validation via Pydantic v2

## 📁 Project Structure

enterprise-saas-api/
├── app/
│ ├── core/ # config, security, logging, middleware, exceptions
│ ├── cache/ # Redis connection and decorators
│ ├── workers/ # Celery app and async tasks
│ ├── metrics/ # Prometheus instrumentation
│ ├── models/ # SQLAlchemy models
│ ├── schemas/ # Pydantic schemas
│ ├── routers/ # API endpoints
│ ├── database.py
│ └── main.py
├── tests/
├── nginx/
├── monitoring/
├── .github/workflows/
├── alembic/
├── docker-compose.yml
└── README.md


## 👨‍💻 Author / Dev

**Sivamani K** — FastAPI Backend Developer
- GitHub: [@sivamani151dev-cell](https://github.com/sivamani151dev-cell)
- Email: sivamani151.dev@gmail.com
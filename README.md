# Auth Module v2 - Production-Grade Authentication Microservice

> Module 01 of a scalable SaaS platform. Python FastAPI backend + React TypeScript frontend + Keycloak IdP.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm
- Docker (for Keycloak)

### One-Command Setup
```bash
python run.py setup   # Install all dependencies
python run.py all     # Start both servers
```

### With Keycloak (Recommended)
```bash
# Start Keycloak (in separate terminal)
cd keycloak
docker-compose up -d

# Start backend & frontend
python run.py all
```

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python server.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📍 Endpoints

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Keycloak Admin | http://localhost:8080/admin (admin/admin) |

## 🔐 API Endpoints

### `POST /api/v1/auth/register`
Register a new user (local mode only).
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### `POST /api/v1/auth/login`
Login and get JWT tokens.
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

Response includes `refresh_token` in Keycloak mode:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 300,
  "refresh_token": "eyJ..."
}
```

### `POST /api/v1/auth/refresh`
Refresh access token (Keycloak mode only).
```json
{
  "refresh_token": "eyJ..."
}
```

### `POST /api/v1/auth/logout`
Logout and invalidate refresh token.
```json
{
  "refresh_token": "eyJ..."
}
```

### `GET /api/v1/auth/me`
Get current user info (requires Bearer token).

Response includes roles in Keycloak mode:
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "roles": ["user", "admin"]
}
```

## 🏗️ Architecture

```
/keycloak                # Keycloak IdP Docker setup
├── docker-compose.yml   # Container configuration
└── realm-export.json    # Pre-configured realm

/auth-client             # Standalone JWT verification library
├── src/auth_client/
│   ├── config.py        # KeycloakConfig dataclass
│   ├── verifier.py      # JWKS fetching + RS256 verification
│   ├── models.py        # AuthUser, TokenPayload
│   └── middleware.py    # FastAPI require_auth dependency
└── pyproject.toml       # pip-installable package

/backend
├── app/
│   ├── api/v1/          # Route handlers
│   ├── core/            # Config, security, Keycloak client
│   ├── db/              # Database setup
│   ├── middleware/      # JWT auth middleware (dual-mode)
│   ├── models/          # ORM models + Pydantic schemas
│   ├── repositories/    # Data access layer (Repository Pattern)
│   └── services/        # Business logic
└── server.py            # Entry point

/frontend
├── src/
│   ├── components/      # Reusable UI components
│   ├── context/         # React Context providers (with roles)
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── router/          # React Router config
│   └── services/        # API client (with token refresh)
```

## 🔧 Tech Stack

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- SQLite via aiosqlite (swappable to PostgreSQL)
- Pydantic v2 (validation)
- python-jose (JWT - RS256 & HS256)
- bcrypt (password hashing - local mode)
- httpx (async HTTP for Keycloak)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router v6
- React Hook Form + Zod
- Tailwind CSS

**Identity Provider:**
- Keycloak 24.0 (Docker)
- RS256 JWT with JWKS
- Realm roles (user, admin)

## 📝 Environment Variables

Copy `backend/.env.example` to `backend/.env` and customize:

```env
APP_ENV=development
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=sqlite+aiosqlite:///./data/auth.db
CORS_ORIGINS=["http://localhost:5173"]

# Auth mode: "local" or "keycloak"
AUTH_MODE=keycloak

# Keycloak settings
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=my-app
KEYCLOAK_CLIENT_ID=my-backend
KEYCLOAK_CLIENT_SECRET=backend-secret-change-in-production
```

## 🔒 Security Features

- ✅ Keycloak IdP integration (RS256 JWT)
- ✅ JWKS-based token verification with caching
- ✅ Refresh token rotation
- ✅ Role-based access control (RBAC)
- ✅ Automatic token refresh in frontend
- ✅ bcrypt password hashing (local mode)
- ✅ Generic error messages (prevents email enumeration)
- ✅ CORS with explicit origins
- ✅ Input validation via Pydantic

## 📦 run.py Commands

```bash
python run.py setup     # Install all dependencies
python run.py backend   # Run backend only
python run.py frontend  # Run frontend only  
python run.py all       # Run both servers
python run.py check     # Verify setup
```

## 🔑 Default Keycloak Users

When using the provided realm export:

| Email | Password | Roles |
|-------|----------|-------|
| testuser@example.com | TestPass123! | user |
| admin@example.com | AdminPass123! | user, admin |

## 🗺️ Future Modules

This module provides extension points for:
- Module 02: User Profile / Settings
- Module 03: Dashboard Content
- Module 04: Billing / Subscriptions
- Module 05: Admin Panel

---

Built with ❤️ following clean architecture principles.

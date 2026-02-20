# Auth Module - Production-Grade Authentication Microservice

> Module 01 of a scalable SaaS platform. Python FastAPI backend + React TypeScript frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### One-Command Setup
```bash
python run.py setup   # Install all dependencies
python run.py all     # Start both servers
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

## 🔐 API Endpoints

### `POST /api/v1/auth/register`
Register a new user.
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### `POST /api/v1/auth/login`
Login and get JWT token.
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### `GET /api/v1/auth/me`
Get current user info (requires Bearer token).

## 🏗️ Architecture

```
/backend
├── app/
│   ├── api/v1/          # Route handlers
│   ├── core/            # Config, security, exceptions
│   ├── db/              # Database setup
│   ├── middleware/      # JWT auth middleware
│   ├── models/          # ORM models + Pydantic schemas
│   ├── repositories/    # Data access layer (Repository Pattern)
│   └── services/        # Business logic
└── server.py            # Entry point

/frontend
├── src/
│   ├── components/      # Reusable UI components
│   ├── context/         # React Context providers
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── router/          # React Router config
│   └── services/        # API client functions
```

## 🔧 Tech Stack

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- SQLite via aiosqlite (swappable to PostgreSQL)
- Pydantic v2 (validation)
- python-jose (JWT)
- passlib + bcrypt (password hashing)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router v6
- React Hook Form + Zod
- Tailwind CSS

## 📝 Environment Variables

Copy `backend/.env.example` to `backend/.env` and customize:

```env
APP_ENV=development
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=sqlite+aiosqlite:///./data/auth.db
CORS_ORIGINS=["http://localhost:5173"]
```

## 🔒 Security Features

- ✅ bcrypt password hashing (12 rounds)
- ✅ JWT access tokens (15min expiry)
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

## 🗺️ Future Modules

This module provides extension points for:
- Module 02: User Profile / Settings
- Module 03: Dashboard Content
- Module 04: Billing / Subscriptions
- Module 05: Admin Panel

---

Built with ❤️ following clean architecture principles.

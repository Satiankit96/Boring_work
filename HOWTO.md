# Auth Module v2 - Senior Engineer Quick Start

## TL;DR

```bash
# Local mode (no Docker)
cd backend && pip install -r requirements.txt
AUTH_MODE=local python server.py

# Separate terminal
cd frontend && npm install && npm run dev
```

- Backend: http://localhost:8000/docs (Swagger)
- Frontend: http://localhost:5173

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  - Token storage in localStorage                                │
│  - Auto refresh on 401                                         │
│  - Role-based UI (isAdmin, hasRole)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐       │
│  │ auth.py     │──▶│ AuthService │──▶│ UserRepository  │       │
│  │ (routes)    │   │             │   │ (SQLite)        │       │
│  └─────────────┘   └──────┬──────┘   └─────────────────┘       │
│                           │                                     │
│                    ┌──────▼──────┐                             │
│                    │ AUTH_MODE   │                             │
│                    └──────┬──────┘                             │
│               ┌───────────┴───────────┐                        │
│               ▼                       ▼                        │
│        ┌─────────────┐         ┌─────────────┐                │
│        │ local       │         │ keycloak    │                │
│        │ (HS256/bcrypt)│       │ (RS256/JWKS)│                │
│        └─────────────┘         └──────┬──────┘                │
└───────────────────────────────────────┼────────────────────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │   Keycloak      │
                               │   (Docker)      │
                               └─────────────────┘
```

---

## Configuration

### Environment Variables (backend/.env)

```bash
# Core
APP_ENV=development
SECRET_KEY=<32+ char secret>

# Auth mode: "local" or "keycloak"
AUTH_MODE=local

# Keycloak (only if AUTH_MODE=keycloak)
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=my-app
KEYCLOAK_CLIENT_ID=my-backend
KEYCLOAK_CLIENT_SECRET=backend-secret-change-in-production
```

---

## Running in Keycloak Mode

```bash
# 1. Start Keycloak (Docker Desktop must be running)
cd keycloak && docker-compose up -d

# 2. Wait for Keycloak startup (~30-60s)
# Check: http://localhost:8080/admin (admin/admin)

# 3. Start backend in keycloak mode
cd backend
AUTH_MODE=keycloak python server.py
```

### Pre-configured Test Users (Keycloak)

| Email                  | Password      | Roles        |
|------------------------|---------------|--------------|
| testuser@example.com   | TestPass123!  | user         |
| admin@example.com      | AdminPass123! | user, admin  |

---

## API Quick Test

```bash
# Register (local mode only)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
# Returns: { access_token, refresh_token (keycloak only), expires_in }

# Get user (with token)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# Refresh token (keycloak only)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Logout (keycloak only)
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/core/config.py` | All settings + Keycloak endpoints |
| `backend/app/core/keycloak_client.py` | Keycloak API calls (httpx) |
| `backend/app/middleware/auth_middleware.py` | JWT validation (dual mode) |
| `backend/app/services/auth_service.py` | Business logic |
| `auth-client/` | Standalone JWKS verification library |
| `keycloak/realm-export.json` | Pre-configured realm |
| `frontend/src/services/auth.api.ts` | API calls + token management |
| `frontend/src/context/AuthContext.tsx` | Global auth state |

---

## Extending

### Add a Protected Route (Backend)

```python
from app.middleware.auth_middleware import get_current_user, require_roles

@router.get("/protected")
async def protected(user = Depends(get_current_user)):
    return {"user_id": user.id, "roles": user.roles}

@router.get("/admin-only")
async def admin_only(
    user = Depends(get_current_user),
    _ = Depends(require_roles("admin"))
):
    return {"admin": user.email}
```

### Check Roles (Frontend)

```tsx
const { isAdmin, hasRole, user } = useAuth();

{isAdmin && <AdminPanel />}
{hasRole("editor") && <EditButton />}
```

---

## Debugging

```bash
# Check backend logs
# (running in terminal shows uvicorn logs)

# Check Keycloak is up
curl http://localhost:8080/realms/my-app/.well-known/openid-configuration

# Decode a JWT (local)
python -c "import jwt; print(jwt.decode('TOKEN', options={'verify_signature':False}))"

# View Keycloak admin console
# http://localhost:8080/admin (admin/admin)
```

---

## Security Notes

1. **Local mode** uses HS256 (symmetric) - `SECRET_KEY` must be 32+ chars
2. **Keycloak mode** uses RS256 (asymmetric) - keys fetched from JWKS endpoint
3. JWKS keys are cached for 1 hour (configurable in `auth-client/config.py`)
4. Refresh tokens auto-rotate in Keycloak mode
5. Frontend auto-refreshes access token on 401

---

## Next Steps

- Replace SQLite with PostgreSQL for production
- Add rate limiting to auth endpoints
- Implement password reset flow
- Add OAuth2 social login (Keycloak supports Google, GitHub, etc.)

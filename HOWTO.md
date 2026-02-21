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

## Integrating Into Your Application

This auth module can serve as a standalone authentication service for your own application. Here's how to integrate it:

### Option 1: Use as Auth Backend (Recommended)

Your application calls this auth service for all authentication needs.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Your Frontend  │────▶│   Auth Module   │────▶│  Your Backend   │
│                 │     │  (this service) │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     │                         │                        │
     │  1. Login/Register      │                        │
     │◀────────────────────────│                        │
     │  2. Get JWT token       │                        │
     │─────────────────────────────────────────────────▶│
     │  3. Call API with token                          │
     │◀─────────────────────────────────────────────────│
     │  4. Response                                     │
```

**Your Backend Integration (Python/FastAPI example):**

```python
import httpx
from fastapi import Depends, HTTPException, Header

AUTH_SERVICE_URL = "http://localhost:8000"

async def verify_token(authorization: str = Header(...)):
    """Verify token by calling auth service's /me endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_SERVICE_URL}/api/v1/auth/me",
            headers={"Authorization": authorization}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()

@app.get("/your-protected-endpoint")
async def protected(user = Depends(verify_token)):
    return {"message": f"Hello {user['email']}"}
```

**Your Backend Integration (Node.js/Express example):**

```javascript
const axios = require('axios');

const AUTH_SERVICE_URL = 'http://localhost:8000';

async function verifyToken(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ error: 'No token' });

    try {
        const response = await axios.get(`${AUTH_SERVICE_URL}/api/v1/auth/me`, {
            headers: { Authorization: authHeader }
        });
        req.user = response.data;
        next();
    } catch (error) {
        return res.status(401).json({ error: 'Invalid token' });
    }
}

app.get('/your-protected-endpoint', verifyToken, (req, res) => {
    res.json({ message: `Hello ${req.user.email}` });
});
```

### Option 2: Direct JWT Verification (Better Performance)

Verify tokens locally without calling the auth service on every request.

**For Local Mode (HS256):**

```python
import jwt
from fastapi import HTTPException

SECRET_KEY = "same-secret-as-auth-service"  # Must match!

def verify_token_local(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**For Keycloak Mode (RS256):**

Use the provided `auth-client` library:

```bash
pip install -e ./auth-client
```

```python
from auth_client import verify_token

# Verifies signature against Keycloak's public keys (JWKS)
user_info = await verify_token(token, issuer="http://localhost:8080/realms/my-app")
print(user_info["email"], user_info["roles"])
```

### Option 3: Embed the Login Page

Use this module's login page and redirect back to your app:

```javascript
// In your frontend app
function loginRedirect() {
    // Save where to return after login
    localStorage.setItem('returnUrl', window.location.href);
    // Redirect to auth module's login page
    window.location.href = 'http://localhost:5173/login';
}

// In the auth module's frontend (after successful login)
// Modify src/pages/Login.tsx to check for returnUrl:
const returnUrl = localStorage.getItem('returnUrl');
if (returnUrl) {
    localStorage.removeItem('returnUrl');
    window.location.href = returnUrl;
}
```

### Sharing Tokens Across Domains

For cross-domain integration:

```javascript
// Option A: Pass token in URL (less secure, use for trusted apps only)
window.location.href = `https://yourapp.com/callback?token=${accessToken}`;

// Option B: Use postMessage for iframe communication
// Auth module
parent.postMessage({ type: 'AUTH_SUCCESS', token: accessToken }, 'https://yourapp.com');

// Your app
window.addEventListener('message', (event) => {
    if (event.origin !== 'http://localhost:5173') return;
    if (event.data.type === 'AUTH_SUCCESS') {
        localStorage.setItem('token', event.data.token);
    }
});
```

### Quick Integration Checklist

1. ✅ Start the auth service (`python run.py --local` or `python run.py`)
2. ✅ Point your app's login button to `http://localhost:5173/login`
3. ✅ After login, read the token from localStorage
4. ✅ Send `Authorization: Bearer <token>` with all API requests
5. ✅ In your backend, verify tokens using Option 1 or Option 2 above
6. ✅ Handle 401 responses by redirecting to login

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

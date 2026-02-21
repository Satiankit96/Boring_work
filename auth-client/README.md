# Auth Client Library

A standalone, pip-installable Python library for JWT verification with Keycloak/OIDC identity providers.

## Features

- **RS256 JWT Verification** - Asymmetric key verification using JWKS endpoints
- **JWKS Caching** - Automatic caching with configurable TTL
- **FastAPI Integration** - Ready-to-use middleware dependency
- **Type-Safe** - Full Pydantic models and type hints
- **Async-First** - Built on httpx for async HTTP operations

## Installation

```bash
pip install auth-client

# With FastAPI support
pip install auth-client[fastapi]
```

## Quick Start

### Configuration

```python
from auth_client import KeycloakConfig, JWKSVerifier

config = KeycloakConfig(
    server_url="http://localhost:8080",
    realm="my-app",
    client_id="my-backend",
    client_secret="your-secret"
)
```

### JWT Verification

```python
from auth_client import JWKSVerifier, KeycloakConfig

config = KeycloakConfig(
    server_url="http://localhost:8080",
    realm="my-app"
)

verifier = JWKSVerifier(config)

# Verify a token
payload = await verifier.verify_token("eyJ...")
print(payload.sub, payload.email, payload.roles)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from auth_client import require_auth, AuthUser, KeycloakConfig

app = FastAPI()
config = KeycloakConfig(
    server_url="http://localhost:8080",
    realm="my-app"
)

@app.get("/protected")
async def protected_route(user: AuthUser = Depends(require_auth(config))):
    return {"message": f"Hello, {user.email}!"}
```

## API Reference

### KeycloakConfig

Configuration dataclass for Keycloak connection:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| server_url | str | Yes | Keycloak server URL |
| realm | str | Yes | Realm name |
| client_id | str | No | Client ID (for token exchange) |
| client_secret | str | No | Client secret (confidential clients) |
| jwks_cache_ttl | int | No | JWKS cache TTL in seconds (default: 3600) |

### JWKSVerifier

Main class for JWT verification:

- `verify_token(token: str) -> TokenPayload` - Verify and decode a JWT
- `get_jwks() -> dict` - Fetch JWKS (with caching)
- `refresh_jwks() -> dict` - Force refresh JWKS cache

### AuthUser

User model returned by middleware:

| Field | Type | Description |
|-------|------|-------------|
| sub | str | Subject (user ID) |
| email | str | None | User's email |
| email_verified | bool | Email verification status |
| preferred_username | str | None | Username |
| roles | list[str] | User's realm roles |
| raw_token | str | Original JWT string |

### Middleware

- `require_auth(config)` - FastAPI dependency requiring valid JWT
- `optional_auth(config)` - FastAPI dependency allowing anonymous access

## License

MIT License

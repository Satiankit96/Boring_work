"""
JWKS-based JWT verification with caching.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
from jose import jwt, JWTError, jwk
from jose.exceptions import JWKError

from auth_client.config import KeycloakConfig
from auth_client.models import TokenPayload


class JWKSVerificationError(Exception):
    """Raised when JWT verification fails."""
    pass


class JWKSFetchError(Exception):
    """Raised when JWKS cannot be fetched."""
    pass


class TokenExpiredError(JWKSVerificationError):
    """Raised when JWT is expired."""
    pass


class InvalidTokenError(JWKSVerificationError):
    """Raised when JWT is malformed or invalid."""
    pass


class InvalidSignatureError(JWKSVerificationError):
    """Raised when JWT signature is invalid."""
    pass


class InvalidIssuerError(JWKSVerificationError):
    """Raised when JWT issuer doesn't match expected."""
    pass


class InvalidAudienceError(JWKSVerificationError):
    """Raised when JWT audience doesn't match expected."""
    pass


class JWKSVerifier:
    """
    JWT verifier using JWKS (JSON Web Key Set) endpoint.
    
    Fetches public keys from Keycloak's JWKS endpoint and uses them
    to verify RS256 signed JWTs. Implements caching with configurable TTL.
    
    Example:
        ```python
        config = KeycloakConfig(
            server_url="http://localhost:8080",
            realm="my-app"
        )
        verifier = JWKSVerifier(config)
        
        try:
            payload = await verifier.verify_token(token)
            print(f"User: {payload.email}")
        except JWKSVerificationError as e:
            print(f"Verification failed: {e}")
        ```
    """
    
    def __init__(self, config: KeycloakConfig):
        """
        Initialize the JWKS verifier.
        
        Args:
            config: Keycloak configuration
        """
        self.config = config
        self._jwks_cache: Optional[dict[str, Any]] = None
        self._jwks_cache_expires: Optional[datetime] = None
        self._cache_lock = asyncio.Lock()
    
    async def get_jwks(self) -> dict[str, Any]:
        """
        Fetch JWKS from Keycloak, using cache if available.
        
        Returns:
            JWKS dictionary containing public keys
            
        Raises:
            JWKSFetchError: If JWKS cannot be fetched
        """
        async with self._cache_lock:
            # Return cached JWKS if still valid
            if self._jwks_cache and self._jwks_cache_expires:
                if datetime.now() < self._jwks_cache_expires:
                    return self._jwks_cache
            
            # Fetch fresh JWKS
            return await self._fetch_jwks()
    
    async def refresh_jwks(self) -> dict[str, Any]:
        """
        Force refresh the JWKS cache.
        
        Returns:
            Fresh JWKS dictionary
            
        Raises:
            JWKSFetchError: If JWKS cannot be fetched
        """
        async with self._cache_lock:
            return await self._fetch_jwks()
    
    async def _fetch_jwks(self) -> dict[str, Any]:
        """
        Fetch JWKS from the endpoint and update cache.
        
        Returns:
            JWKS dictionary
            
        Raises:
            JWKSFetchError: If fetch fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.config.jwks_uri,
                    timeout=10.0
                )
                response.raise_for_status()
                
                jwks = response.json()
                
                # Update cache
                self._jwks_cache = jwks
                self._jwks_cache_expires = datetime.now() + timedelta(
                    seconds=self.config.jwks_cache_ttl
                )
                
                return jwks
                
        except httpx.HTTPError as e:
            raise JWKSFetchError(f"Failed to fetch JWKS from {self.config.jwks_uri}: {e}")
        except Exception as e:
            raise JWKSFetchError(f"Unexpected error fetching JWKS: {e}")
    
    def _get_signing_key(self, token: str, jwks: dict[str, Any]) -> dict[str, Any]:
        """
        Get the appropriate signing key from JWKS for the given token.
        
        Args:
            token: JWT token string
            jwks: JWKS dictionary
            
        Returns:
            The matching key from JWKS
            
        Raises:
            InvalidTokenError: If token header is invalid
            JWKSVerificationError: If no matching key found
        """
        try:
            # Decode header without verification to get kid
            unverified_header = jwt.get_unverified_header(token)
        except JWTError as e:
            raise InvalidTokenError(f"Invalid token header: {e}")
        
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")
        
        if alg != "RS256":
            raise InvalidTokenError(f"Unsupported algorithm: {alg}. Only RS256 is supported.")
        
        # Find matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        
        raise JWKSVerificationError(
            f"No matching key found in JWKS for kid: {kid}"
        )
    
    async def verify_token(
        self,
        token: str,
        *,
        verify_exp: bool = True,
        verify_iss: bool = True,
        verify_aud: bool | None = None,
    ) -> TokenPayload:
        """
        Verify a JWT token and return decoded payload.
        
        Args:
            token: JWT token string (without "Bearer " prefix)
            verify_exp: Whether to verify expiration (default: True)
            verify_iss: Whether to verify issuer (default: True)
            verify_aud: Whether to verify audience (default: from config)
            
        Returns:
            TokenPayload with decoded claims
            
        Raises:
            TokenExpiredError: If token is expired
            InvalidTokenError: If token is malformed
            InvalidSignatureError: If signature verification fails
            InvalidIssuerError: If issuer doesn't match
            InvalidAudienceError: If audience doesn't match
            JWKSVerificationError: For other verification failures
        """
        if not token:
            raise InvalidTokenError("Token is empty")
        
        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Get JWKS
        jwks = await self.get_jwks()
        
        # Get signing key
        signing_key = self._get_signing_key(token, jwks)
        
        # Build verification options
        options = {
            "verify_signature": True,
            "verify_exp": verify_exp,
            "verify_iss": verify_iss,
            "verify_aud": verify_aud if verify_aud is not None else self.config.verify_audience,
            "require_exp": True,
            "require_iat": True,
            "require_sub": True,
        }
        
        # Build expected values
        audience = self.config.get_audience() if options["verify_aud"] else None
        
        try:
            # Verify and decode
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=audience,
                issuer=self.config.issuer if verify_iss else None,
                options=options,
            )
            
            return TokenPayload.from_claims(claims)
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.JWTClaimsError as e:
            error_msg = str(e).lower()
            if "issuer" in error_msg:
                raise InvalidIssuerError(f"Invalid issuer: {e}")
            elif "audience" in error_msg:
                raise InvalidAudienceError(f"Invalid audience: {e}")
            raise JWKSVerificationError(f"Claims validation failed: {e}")
        except JWTError as e:
            if "signature" in str(e).lower():
                raise InvalidSignatureError(f"Invalid signature: {e}")
            raise InvalidTokenError(f"Token verification failed: {e}")
        except Exception as e:
            raise JWKSVerificationError(f"Unexpected verification error: {e}")
    
    async def verify_token_with_retry(
        self,
        token: str,
        **kwargs
    ) -> TokenPayload:
        """
        Verify token with automatic JWKS refresh on key not found.
        
        If verification fails due to missing key, this method will
        refresh the JWKS cache and retry once.
        
        Args:
            token: JWT token string
            **kwargs: Additional arguments for verify_token
            
        Returns:
            TokenPayload with decoded claims
        """
        try:
            return await self.verify_token(token, **kwargs)
        except JWKSVerificationError as e:
            if "No matching key found" in str(e):
                # Key might have rotated, refresh JWKS and retry
                await self.refresh_jwks()
                return await self.verify_token(token, **kwargs)
            raise

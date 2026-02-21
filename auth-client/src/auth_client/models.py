"""
Data models for authentication.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class TokenPayload:
    """
    Decoded JWT token payload.
    
    Attributes:
        sub: Subject (user ID)
        iss: Token issuer
        aud: Audience (can be string or list)
        exp: Expiration timestamp
        iat: Issued at timestamp
        jti: JWT ID
        typ: Token type
        azp: Authorized party (client ID)
        scope: Token scope
        email: User's email
        email_verified: Whether email is verified
        preferred_username: User's preferred username
        given_name: User's first name
        family_name: User's last name
        name: User's full name
        roles: List of realm roles
        resource_access: Client-specific roles
        raw_claims: Original raw claims dictionary
    """
    
    sub: str
    iss: str
    exp: int
    iat: int
    aud: str | list[str] | None = None
    jti: Optional[str] = None
    typ: Optional[str] = None
    azp: Optional[str] = None
    scope: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    name: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    resource_access: dict[str, Any] = field(default_factory=dict)
    raw_claims: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> "TokenPayload":
        """
        Create a TokenPayload from raw JWT claims.
        
        Args:
            claims: Dictionary of JWT claims
            
        Returns:
            TokenPayload instance
        """
        # Extract realm roles from realm_access
        roles: list[str] = []
        if "realm_access" in claims and "roles" in claims["realm_access"]:
            roles = claims["realm_access"]["roles"]
        # Also check for direct roles claim
        elif "roles" in claims:
            roles = claims["roles"] if isinstance(claims["roles"], list) else []
        
        return cls(
            sub=claims.get("sub", ""),
            iss=claims.get("iss", ""),
            exp=claims.get("exp", 0),
            iat=claims.get("iat", 0),
            aud=claims.get("aud"),
            jti=claims.get("jti"),
            typ=claims.get("typ"),
            azp=claims.get("azp"),
            scope=claims.get("scope"),
            email=claims.get("email"),
            email_verified=claims.get("email_verified", False),
            preferred_username=claims.get("preferred_username"),
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
            name=claims.get("name"),
            roles=roles,
            resource_access=claims.get("resource_access", {}),
            raw_claims=claims,
        )
    
    @property
    def expires_at(self) -> datetime:
        """Get expiration as datetime."""
        return datetime.fromtimestamp(self.exp)
    
    @property
    def issued_at(self) -> datetime:
        """Get issued at as datetime."""
        return datetime.fromtimestamp(self.iat)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() > self.expires_at
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific realm role."""
        return role in self.roles
    
    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.roles for role in roles)


@dataclass
class AuthUser:
    """
    Authenticated user model for use in application code.
    
    This is a simplified view of the TokenPayload suitable for
    use in route handlers and business logic.
    
    Attributes:
        sub: Subject (user ID from Keycloak)
        email: User's email address
        email_verified: Whether email is verified
        username: User's username (preferred_username)
        name: User's full name
        given_name: User's first name
        family_name: User's last name
        roles: List of realm roles
        raw_token: Original JWT string
        token_payload: Full token payload for advanced use
    """
    
    sub: str
    email: Optional[str]
    email_verified: bool
    username: Optional[str]
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    roles: list[str]
    raw_token: str
    token_payload: TokenPayload
    
    @classmethod
    def from_token_payload(cls, payload: TokenPayload, raw_token: str) -> "AuthUser":
        """
        Create an AuthUser from a TokenPayload.
        
        Args:
            payload: Decoded token payload
            raw_token: Original JWT string
            
        Returns:
            AuthUser instance
        """
        return cls(
            sub=payload.sub,
            email=payload.email,
            email_verified=payload.email_verified,
            username=payload.preferred_username,
            name=payload.name,
            given_name=payload.given_name,
            family_name=payload.family_name,
            roles=payload.roles,
            raw_token=raw_token,
            token_payload=payload,
        )
    
    @property
    def id(self) -> str:
        """Alias for sub (user ID)."""
        return self.sub
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.roles for role in roles)

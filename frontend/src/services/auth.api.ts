/**
 * Auth API Service
 * =================
 * Role: All HTTP calls to the backend auth API.
 * This is the ONLY place fetch() is used for auth endpoints.
 * Supports both local and Keycloak authentication modes.
 * Other components/hooks import this — never call fetch directly.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Types
export interface User {
  id: string;
  email: string | null;
  roles?: string[];
  created_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user?: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
}

export interface MeResponse {
  id: string;
  email: string | null;
  roles: string[];
  created_at: string | null;
}

export interface ApiError {
  detail: {
    code: string;
    message: string;
  };
}

// =============================================================================
// Token Management
// =============================================================================

/**
 * Store tokens in localStorage.
 */
export function storeTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Get stored access token.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get stored refresh token.
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Clear all stored tokens.
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if user has tokens stored.
 */
export function hasStoredTokens(): boolean {
  return !!getAccessToken();
}

// =============================================================================
// API Calls
// =============================================================================

/**
 * Register a new user account.
 */
export async function register(email: string, password: string): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail.message || 'Registration failed');
  }

  return response.json();
}

/**
 * Login and get access token (and refresh token in Keycloak mode).
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail.message || 'Login failed');
  }

  const data: LoginResponse = await response.json();
  
  // Store tokens
  storeTokens(data.access_token, data.refresh_token);
  
  return data;
}

/**
 * Refresh the access token using the stored refresh token.
 */
export async function refreshAccessToken(): Promise<RefreshResponse | null> {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    return null;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh failed - clear tokens
      clearTokens();
      return null;
    }

    const data: RefreshResponse = await response.json();
    
    // Store new tokens
    storeTokens(data.access_token, data.refresh_token);
    
    return data;
  } catch {
    clearTokens();
    return null;
  }
}

/**
 * Logout and invalidate refresh token.
 */
export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  
  if (refreshToken) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Ignore logout errors - just clear local tokens
    }
  }
  
  clearTokens();
}

/**
 * Get current user info (requires valid token).
 * Automatically attempts token refresh on 401.
 */
export async function getMe(token?: string): Promise<MeResponse> {
  const accessToken = token || getAccessToken();
  
  if (!accessToken) {
    throw new Error('No access token available');
  }
  
  let response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  // Try to refresh token on 401
  if (response.status === 401) {
    const refreshResult = await refreshAccessToken();
    
    if (refreshResult) {
      // Retry with new token
      response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${refreshResult.access_token}`,
        },
      });
    }
  }

  if (!response.ok) {
    throw new Error('Failed to get user info');
  }

  return response.json();
}

/**
 * Create an authenticated fetch wrapper that handles token refresh.
 */
export async function authFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const accessToken = getAccessToken();
  
  if (!accessToken) {
    throw new Error('Not authenticated');
  }
  
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${accessToken}`);
  
  let response = await fetch(url, { ...options, headers });
  
  // Try to refresh on 401
  if (response.status === 401) {
    const refreshResult = await refreshAccessToken();
    
    if (refreshResult) {
      headers.set('Authorization', `Bearer ${refreshResult.access_token}`);
      response = await fetch(url, { ...options, headers });
    }
  }
  
  return response;
}

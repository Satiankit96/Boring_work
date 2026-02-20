/**
 * Auth API Service
 * =================
 * Role: All HTTP calls to the backend auth API.
 * This is the ONLY place fetch() is used for auth endpoints.
 * Other components/hooks import this — never call fetch directly.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
}

export interface ApiError {
  detail: {
    code: string;
    message: string;
  };
}

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
 * Login and get access token.
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

  return response.json();
}

/**
 * Get current user info (requires valid token).
 */
export async function getMe(token: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get user info');
  }

  return response.json();
}

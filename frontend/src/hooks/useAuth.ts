/**
 * useAuth Hook
 * ============
 * Role: Convenient hook for authentication operations.
 * Wraps AuthContext and adds additional utility functions.
 */

import { useState } from 'react';
import { useAuthContext } from '../context/AuthContext';
import { register as apiRegister } from '../services/auth.api';

export function useAuth() {
  const auth = useAuthContext();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Login with email and password.
   * Returns true on success, false on failure.
   */
  const login = async (email: string, password: string): Promise<boolean> => {
    setError(null);
    setIsSubmitting(true);

    try {
      await auth.login(email, password);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Register a new account.
   * Returns true on success, false on failure.
   */
  const register = async (email: string, password: string): Promise<boolean> => {
    setError(null);
    setIsSubmitting(true);

    try {
      await apiRegister(email, password);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Logout current user.
   */
  const logout = async (): Promise<void> => {
    await auth.logout();
  };

  /**
   * Clear any error state.
   */
  const clearError = () => {
    setError(null);
  };

  /**
   * Check if user has a specific role.
   */
  const hasRole = (role: string): boolean => {
    return auth.hasRole(role);
  };

  return {
    // State
    user: auth.user,
    isAuthenticated: auth.isAuthenticated,
    isLoading: auth.isLoading,
    isSubmitting,
    error,
    isAdmin: auth.isAdmin,

    // Actions
    login,
    register,
    logout,
    clearError,
    hasRole,
  };
}

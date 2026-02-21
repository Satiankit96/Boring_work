/**
 * Auth Context Provider
 * =====================
 * Role: Global authentication state management.
 * Provides user state, login/logout functions to entire app.
 * Supports both local and Keycloak authentication modes.
 * Uses Context API + useReducer — no external state libraries needed.
 */

import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import {
  login as apiLogin,
  logout as apiLogout,
  getMe,
  clearTokens,
  hasStoredTokens,
} from '../services/auth.api';

// User type from /me endpoint
interface User {
  id: string;
  email: string | null;
  roles: string[];
  created_at: string | null;
}

// State types
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Action types
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User } }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'RESTORE_SESSION'; payload: { user: User } }
  | { type: 'SET_LOADING'; payload: boolean };

// Initial state
const initialState: AuthState = {
  user: null,
  isLoading: true, // Start loading to check for existing session
  isAuthenticated: false,
};

// Reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true };
    case 'LOGIN_SUCCESS':
    case 'RESTORE_SESSION':
      return {
        ...state,
        user: action.payload.user,
        isLoading: false,
        isAuthenticated: true,
      };
    case 'LOGIN_FAILURE':
      return { ...state, isLoading: false };
    case 'LOGOUT':
      return { ...initialState, isLoading: false };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    default:
      return state;
  }
}

// Context
interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      if (!hasStoredTokens()) {
        dispatch({ type: 'LOGOUT' });
        return;
      }
      
      try {
        const meResponse = await getMe();
        const user: User = {
          id: meResponse.id,
          email: meResponse.email,
          roles: meResponse.roles || [],
          created_at: meResponse.created_at,
        };
        dispatch({ type: 'RESTORE_SESSION', payload: { user } });
      } catch {
        // Token invalid, clear it
        clearTokens();
        dispatch({ type: 'LOGOUT' });
      }
    };

    restoreSession();
  }, []);

  // Login function
  const login = async (email: string, password: string): Promise<void> => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      await apiLogin(email, password);
      
      // Get user info from /me endpoint (tokens are already stored by apiLogin)
      const meResponse = await getMe();
      const user: User = {
        id: meResponse.id,
        email: meResponse.email,
        roles: meResponse.roles || [],
        created_at: meResponse.created_at,
      };
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user },
      });
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' });
      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    await apiLogout();
    dispatch({ type: 'LOGOUT' });
  };

  // Check if user has a specific role
  const hasRole = (role: string): boolean => {
    return state.user?.roles?.includes(role) ?? false;
  };

  // Check if user is admin
  const isAdmin = hasRole('admin');

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    hasRole,
    isAdmin,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for using auth context
export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  
  return context;
}

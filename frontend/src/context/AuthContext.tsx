/**
 * Auth Context Provider
 * =====================
 * Role: Global authentication state management.
 * Provides user state, login/logout functions to entire app.
 * Uses Context API + useReducer — no external state libraries needed.
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { User, login as apiLogin, getMe } from '../services/auth.api';

// State types
interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Action types
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'RESTORE_SESSION'; payload: { user: User; token: string } };

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
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
        token: action.payload.token,
        isLoading: false,
        isAuthenticated: true,
      };
    case 'LOGIN_FAILURE':
      return { ...state, isLoading: false };
    case 'LOGOUT':
      return { ...initialState, isLoading: false };
    default:
      return state;
  }
}

// Context
interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token storage key
const TOKEN_KEY = 'auth_token';

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      
      if (storedToken) {
        try {
          const user = await getMe(storedToken);
          dispatch({ type: 'RESTORE_SESSION', payload: { user, token: storedToken } });
        } catch {
          // Token invalid, clear it
          localStorage.removeItem(TOKEN_KEY);
          dispatch({ type: 'LOGOUT' });
        }
      } else {
        dispatch({ type: 'LOGOUT' });
      }
    };

    restoreSession();
  }, []);

  // Login function
  const login = async (email: string, password: string): Promise<void> => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await apiLogin(email, password);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user: response.user, token: response.access_token },
      });
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' });
      throw error;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    dispatch({ type: 'LOGOUT' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
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

/**
 * Login Page
 * ==========
 * Role: Page component for authentication (login/register toggle).
 * Redirects authenticated users to dashboard.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginForm, RegisterForm } from '../components/AuthForm';
import { useAuth } from '../hooks/useAuth';

type AuthMode = 'login' | 'register';

export function LoginPage() {
  const [mode, setMode] = useState<AuthMode>('login');
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSuccess = () => {
    if (mode === 'register') {
      // After registration, switch to login
      setMode('login');
    } else {
      // After login, redirect to dashboard
      navigate('/dashboard', { replace: true });
    }
  };

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        {mode === 'login' ? (
          <LoginForm
            onSuccess={handleSuccess}
            onSwitchToRegister={() => setMode('register')}
          />
        ) : (
          <RegisterForm
            onSuccess={handleSuccess}
            onSwitchToLogin={() => setMode('login')}
          />
        )}
      </div>
    </div>
  );
}

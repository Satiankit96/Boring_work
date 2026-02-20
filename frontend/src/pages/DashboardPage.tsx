/**
 * Dashboard Page
 * ==============
 * Role: Protected page shown after successful login.
 * Currently a placeholder — future modules will add real content.
 */

import { useAuth } from '../hooks/useAuth';

export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Welcome, {user?.email}! 🎉
          </h2>
          <p className="text-gray-600 mb-6">
            You've successfully authenticated. This is a placeholder dashboard.
          </p>
          <div className="inline-block bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 font-medium">
              📦 Module 01: Authentication — Complete
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Next modules: User Profile, Settings, Billing...
            </p>
          </div>
        </div>

        {/* User Info Card */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Account</h3>
          <dl className="space-y-2">
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">User ID:</dt>
              <dd className="text-sm text-gray-900 font-mono">{user?.id}</dd>
            </div>
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">Email:</dt>
              <dd className="text-sm text-gray-900">{user?.email}</dd>
            </div>
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">Joined:</dt>
              <dd className="text-sm text-gray-900">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </dd>
            </div>
          </dl>
        </div>
      </main>
    </div>
  );
}

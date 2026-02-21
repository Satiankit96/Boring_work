/**
 * Dashboard Page
 * ==============
 * Role: Protected page shown after successful login.
 * Currently a placeholder — future modules will add real content.
 * Displays user info including roles from Keycloak if available.
 */

import { useAuth } from '../hooks/useAuth';

export function DashboardPage() {
  const { user, logout, isAdmin } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email || 'User'}</span>
            {isAdmin && (
              <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                Admin
              </span>
            )}
            <button
              onClick={handleLogout}
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
            Welcome{user?.email ? `, ${user.email}` : ''}! 🎉
          </h2>
          <p className="text-gray-600 mb-6">
            You've successfully authenticated. This is a placeholder dashboard.
          </p>
          <div className="inline-block bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 font-medium">
              📦 Module 01: Authentication v2 — Complete
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Now with Keycloak integration and role-based access!
            </p>
          </div>
        </div>

        {/* User Info Card */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Account</h3>
          <dl className="space-y-2">
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">User ID:</dt>
              <dd className="text-sm text-gray-900 font-mono">{user?.id || 'N/A'}</dd>
            </div>
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">Email:</dt>
              <dd className="text-sm text-gray-900">{user?.email || 'N/A'}</dd>
            </div>
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">Roles:</dt>
              <dd className="text-sm text-gray-900">
                {user?.roles && user.roles.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {user.roles.map((role) => (
                      <span
                        key={role}
                        className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded"
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-gray-400">No roles assigned</span>
                )}
              </dd>
            </div>
            <div className="flex">
              <dt className="w-24 text-sm text-gray-500">Joined:</dt>
              <dd className="text-sm text-gray-900">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </dd>
            </div>
          </dl>
        </div>

        {/* Admin Section (only visible to admins) */}
        {isAdmin && (
          <div className="mt-8 bg-purple-50 border border-purple-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-900 mb-2">
              🔐 Admin Section
            </h3>
            <p className="text-sm text-purple-700">
              You have admin privileges. This section is only visible to administrators.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

/**
 * Application Entry Point
 * =======================
 * Role: Root React component that wraps the app with providers.
 */

import { AuthProvider } from './context/AuthContext';
import { AppRouter } from './router';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;

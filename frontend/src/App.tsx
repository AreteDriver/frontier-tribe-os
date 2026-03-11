import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Landing from './pages/Landing';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';
import Roster from './pages/Roster';
import Production from './pages/Production';
import Treasury from './pages/Treasury';
import Watch from './pages/Watch';
import KillFeed from './pages/KillFeed';
import Alerts from './pages/Alerts';
import Systems from './pages/Systems';
import Layout from './components/Layout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <ErrorBoundary>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/roster" element={<Roster />} />
          <Route path="/production" element={<Production />} />
          <Route path="/treasury" element={<Treasury />} />
          <Route path="/watch" element={<Watch />} />
          <Route path="/intel" element={<KillFeed />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/systems" element={<Systems />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;

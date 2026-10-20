import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Route guard that redirects unauthenticated users to the login page.
 * Preserves the intended destination so the user is redirected back after login.
 */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!user) {
    // Redirect to login with the intended destination preserved in state
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

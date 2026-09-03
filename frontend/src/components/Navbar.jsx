import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="border-b border-gray-200 bg-white">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center space-x-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600">
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span className="text-lg font-bold text-gray-900">Resume<span className="text-primary-600">Score</span></span>
        </Link>

        <div className="flex items-center space-x-4">
          <Link to="/upload" className="hidden text-sm font-medium text-gray-700 hover:text-primary-600 sm:block">
            Analyze
          </Link>
          {user ? (
            <>
              <Link to="/history" className="hidden text-sm font-medium text-gray-700 hover:text-primary-600 sm:block">
                History
              </Link>
              <span className="hidden text-sm text-gray-500 sm:block">{user.username}</span>
              <button onClick={handleLogout} className="btn-secondary py-1.5 px-3 text-sm">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary py-1.5 px-3 text-sm">
                Login
              </Link>
              <Link to="/register" className="btn-primary py-1.5 px-3 text-sm">
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

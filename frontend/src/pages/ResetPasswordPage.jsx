import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ResetPasswordPage() {
  const { resetPassword } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [token, setToken] = useState(searchParams.get("token") || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // null | "pending" | "success" | "error"
  const [errorMessage, setErrorMessage] = useState("");
  const [manualToken, setManualToken] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token.trim()) {
      setErrorMessage("Reset token is missing.");
      setResult("error");
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setErrorMessage("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    setErrorMessage("");
    try {
      await resetPassword(token.trim(), newPassword);
      setResult("success");
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || "Password reset failed.");
      setResult("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16 sm:px-6">
      <div className="card">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Set a new password</h1>
          <p className="mt-1 text-sm text-gray-600">
            Choose a strong password for your account.
          </p>
        </div>

        {result === "success" && (
          <div className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
            <p className="font-medium">Password reset successfully!</p>
            <p className="mt-1">You can now log in with your new password.</p>
            <Link to="/login" className="mt-3 inline-block btn-primary">
              Go to login
            </Link>
          </div>
        )}

        {result === "error" && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
            <p className="font-medium">Reset failed</p>
            <p className="mt-1">{errorMessage}</p>
          </div>
        )}

        {result === null && (
          <>
            {!manualToken ? (
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  If your email client opened this page, the reset should happen
                  automatically. Otherwise, paste the token from your email below.
                </p>
                <button
                  onClick={() => setManualToken(true)}
                  className="mt-3 text-sm font-medium text-primary-600 hover:text-primary-700"
                >
                  Enter token manually
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="token" className="block text-sm font-medium text-gray-700">
                    Reset token
                  </label>
                  <input
                    id="token"
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    className="input-field mt-1"
                    placeholder="Paste your reset token"
                  />
                </div>
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                    New password
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input-field mt-1"
                    placeholder="••••••••"
                  />
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                    Confirm password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input-field mt-1"
                    placeholder="••••••••"
                  />
                </div>
                {submitting ? (
                  <p className="text-sm text-gray-500">Resetting password...</p>
                ) : (
                  <button type="submit" className="btn-primary w-full">
                    Reset password
                  </button>
                )}
              </form>
            )}
          </>
        )}

        <p className="mt-4 text-center text-sm text-gray-600">
          <Link to="/forgot-password" className="font-medium text-primary-600 hover:text-primary-700">
            Request a new link
          </Link>
        </p>
      </div>
    </div>
  );
}
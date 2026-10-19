import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ResendVerificationPage() {
  const { resendVerification } = useAuth();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await resendVerification(email);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to resend verification.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16 sm:px-6">
      <div className="card">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Resend verification email</h1>
          <p className="mt-1 text-sm text-gray-600">
            Enter your email address to receive a new verification link.
          </p>
        </div>

        {submitted ? (
          <div className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
            <p className="font-medium">Check your inbox</p>
            <p className="mt-1">
              If an account exists for <strong>{email}</strong>, a new verification
              link has been sent.
            </p>
            <Link to="/login" className="mt-3 inline-block btn-primary">
              Back to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field mt-1"
                placeholder="you@example.com"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? "Sending..." : "Send verification email"}
            </button>
          </form>
        )}

        <p className="mt-4 text-center text-sm text-gray-600">
          <Link to="/login" className="font-medium text-primary-600 hover:text-primary-700">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function VerifyEmailPage() {
  const { verifyEmail } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [token, setToken] = useState(searchParams.get("token") || "");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // null | "pending" | "success" | "error"
  const [errorMessage, setErrorMessage] = useState("");
  const [manualToken, setManualToken] = useState(false);

  // Auto-submit if a token is present in the URL
  useEffect(() => {
    const urlToken = searchParams.get("token");
    if (urlToken && result === null) {
      setToken(urlToken);
      setSubmitting(true);
      verifyEmail(urlToken)
        .then(() => setResult("success"))
        .catch((err) => {
          setErrorMessage(err.response?.data?.detail || "Verification failed.");
          setResult("error");
        })
        .finally(() => setSubmitting(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token.trim()) {
      setErrorMessage("Verification token is missing.");
      setResult("error");
      return;
    }
    setSubmitting(true);
    setErrorMessage("");
    try {
      await verifyEmail(token.trim());
      setResult("success");
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || "Verification failed.");
      setResult("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col justify-center px-4 py-16 sm:px-6">
      <div className="card">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Verify your email</h1>
          <p className="mt-1 text-sm text-gray-600">
            Click the link in your verification email to confirm your address.
          </p>
        </div>

        {result === "success" && (
          <div className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
            <p className="font-medium">Email verified successfully!</p>
            <p className="mt-1">You can now log in to your account.</p>
            <Link to="/login" className="mt-3 inline-block btn-primary">
              Go to login
            </Link>
          </div>
        )}

        {result === "error" && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800">
            <p className="font-medium">Verification failed</p>
            <p className="mt-1">{errorMessage}</p>
          </div>
        )}

        {result === null && (
          <>
            {!manualToken ? (
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  If your email client opened this page, the verification should happen
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
                    Verification token
                  </label>
                  <input
                    id="token"
                    type="text"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    className="input-field mt-1"
                    placeholder="Paste your verification token"
                  />
                </div>
                {submitting ? (
                  <p className="text-sm text-gray-500">Verifying...</p>
                ) : (
                  <button type="submit" className="btn-primary w-full">
                    Verify email
                  </button>
                )}
              </form>
            )}
          </>
        )}

        <p className="mt-4 text-center text-sm text-gray-600">
          Didn't receive an email?{" "}
          <Link to="/resend-verification" className="font-medium text-primary-600 hover:text-primary-700">
            Resend verification
          </Link>
        </p>
      </div>
    </div>
  );
}
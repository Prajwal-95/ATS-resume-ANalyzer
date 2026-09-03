import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { analysisApi } from "../services/api";
import { useAuth } from "../context/AuthContext";
import Badge from "../components/Badge";

export default function HistoryPage() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    loadHistory();
  }, [user]);

  const loadHistory = async () => {
    try {
      const data = await analysisApi.history();
      setAnalyses(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this analysis? This cannot be undone.")) return;
    try {
      await analysisApi.delete(id);
      setAnalyses((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      setError("Failed to delete analysis");
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-gray-500">Loading...</div>;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Previous Resume Analyses</h1>
          <p className="mt-1 text-sm text-gray-600">
            All your past resume analyses, saved securely to your account.
          </p>
        </div>
        <Link to="/upload" className="btn-primary">New Analysis</Link>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {analyses.length === 0 ? (
        <div className="card text-center py-16">
          <div className="text-4xl">📋</div>
          <h2 className="mt-4 text-lg font-medium text-gray-900">No analyses yet</h2>
          <p className="mt-1 text-sm text-gray-500">
            Upload your first resume to see your ATS score.
          </p>
          <Link to="/upload" className="btn-primary mt-6">Analyze Your Resume</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {analyses.map((a) => (
            <div key={a.id} className="card flex items-center justify-between">
              <button
                className="flex-1 text-left"
                onClick={() => navigate(`/results/${a.id}`)}
              >
                <div className="flex items-center gap-4">
                  <Badge status={a.total_score >= 80 ? "excellent" : a.total_score >= 60 ? "good" : "warning"}>
                    {Math.round(a.total_score)}/100
                  </Badge>
                  <div>
                    <p className="font-medium text-gray-900">{a.resume_filename || "Untitled resume"}</p>
                    {a.job_title && <p className="text-sm text-gray-500">{a.job_title}</p>}
                  </div>
                </div>
                <p className="mt-1 text-xs text-gray-400">
                  {new Date(a.created_at).toLocaleString()}
                </p>
              </button>
              <button
                onClick={() => handleDelete(a.id)}
                className="ml-4 text-sm text-red-600 hover:text-red-700"
                aria-label="Delete analysis"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

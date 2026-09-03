import { useState, useRef, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { resumeApi } from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import { demoResume, demoJobDescription } from "../utils/demoData";

export default function UploadPage() {
  const [searchParams] = useSearchParams();
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDemo = async () => {
    setError("");
    setLoading(true);
    try {
      const result = await resumeApi.demo(demoResume, demoJobDescription);
      navigate(`/results/${result.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Demo analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setError("");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      setError("");
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload a resume file (PDF or DOCX).");
      return;
    }
    if (!jobDescription.trim()) {
      setError("Please paste a job description.");
      return;
    }

    setError("");
    setLoading(true);
    try {
      const result = await resumeApi.analyze(file, jobDescription);
      navigate(`/results/${result.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Auto-trigger demo if user navigated with ?demo=1
  const autoDemoTriggered = useRef(false);
  useEffect(() => {
    if (searchParams.get("demo") === "1" && !autoDemoTriggered.current) {
      autoDemoTriggered.current = true;
      handleDemo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <div className="card text-center">
          <h2 className="text-xl font-semibold text-gray-900">Analyzing your resume</h2>
          <LoadingScreen />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">Analyze Your Resume</h1>
        <p className="mt-2 text-gray-600">Upload your resume and paste the job description to get your ATS score.</p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Resume upload */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">1. Upload Resume</h2>
          <p className="mt-1 text-sm text-gray-500">Supported formats: PDF, DOCX. Max 10MB.</p>

          <div
            className={`mt-4 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              dragging ? "border-primary-500 bg-primary-50" : "border-gray-300 hover:border-primary-400"
            }`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <div className="text-4xl">📄</div>
            <p className="mt-3 text-sm font-medium text-gray-700">
              {file ? file.name : "Drag & drop your resume here"}
            </p>
            {!file && <p className="mt-1 text-xs text-gray-400">or click to browse files</p>}
            {file && (
              <button
                className="mt-2 text-xs font-medium text-primary-600 hover:text-primary-700"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
              >
                Remove file
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        </div>

        {/* Job description */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">2. Paste Job Description</h2>
          <p className="mt-1 text-sm text-gray-500">Copy and paste the full job posting here.</p>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            rows={10}
            className="input-field mt-4 min-h-[200px] resize-y"
          />
        </div>
      </div>

      {/* Buttons */}
      <div className="mt-8 flex flex-col items-center gap-4">
        <button onClick={handleAnalyze} className="btn-primary w-full px-10 py-3 text-base sm:w-auto" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
        <button onClick={handleDemo} className="text-sm font-medium text-primary-600 hover:text-primary-700">
          Try Demo with sample data
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}

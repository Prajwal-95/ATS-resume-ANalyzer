import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { resumeApi } from "../services/api";
import LoadingScreen from "../components/LoadingScreen";
import { demoResume, demoJobDescription } from "../utils/demoData";

const MAX_FILE_SIZE_MB = 10;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];

export default function UploadPage() {
  const [searchParams] = useSearchParams();
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const validateFile = useCallback((selectedFile) => {
    if (!selectedFile) return "Please select a file.";
    const ext = "." + selectedFile.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return "Unsupported file type. Please upload a PDF or DOCX file.";
    }
    if (selectedFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum size is ${MAX_FILE_SIZE_MB} MB.`;
    }
    return null;
  }, []);

  const handleDemo = async () => {
    if (loading) return;
    setError("");
    setLoading(true);
    try {
      const result = await resumeApi.demo(demoResume, demoJobDescription);
      navigate(`/results/${result.id}`);
    } catch (err) {
      // Demo uses the shared analysis backend; report a useful, safe error
      // without exposing server internals.
      if (!err.response) {
        setError("The backend is unavailable. Please try again later.");
      } else if (err.response.status === 429) {
        setError("Demo requests are rate-limited. Please wait a moment and try again.");
      } else if (err.response.status >= 500) {
        setError("The demo service encountered an error. Please try again later.");
      } else {
        setError(err.response?.data?.detail || "Demo analysis failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const validationError = validateFile(selected);
      if (validationError) {
        setError(validationError);
        return;
      }
      setFile(selected);
      setError("");
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      const validationError = validateFile(dropped);
      if (validationError) {
        setError(validationError);
        return;
      }
      setFile(dropped);
      setError("");
    }
  };

  const handleAnalyze = async () => {
    if (loading) return;
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
    setUploadProgress(0);
    try {
      const result = await resumeApi.analyze(file, jobDescription, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        }
      });
      navigate(`/results/${result.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
      setUploadProgress(0);
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
          {uploadProgress > 0 && uploadProgress < 100 ? (
            <div className="mt-4">
              <div className="mx-auto h-2 w-48 overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-primary-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-2 text-sm text-gray-500">Uploading... {uploadProgress}%</p>
            </div>
          ) : (
            <p className="mt-2 text-sm text-gray-500">Processing your resume...</p>
          )}
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
            role="button"
            tabIndex={0}
            aria-label="Upload resume file"
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click(); }}
          >
            <div className="text-4xl" aria-hidden="true">📄</div>
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
              aria-label="Choose resume file"
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
            aria-label="Job description"
          />
          <p className="mt-1 text-xs text-gray-400">{jobDescription.length} characters</p>
        </div>
      </div>

      {/* Buttons */}
      <div className="mt-8 flex flex-col items-center gap-4">
        <button onClick={handleAnalyze} className="btn-primary w-full px-10 py-3 text-base sm:w-auto" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
        <button onClick={handleDemo} className="text-sm font-medium text-primary-600 hover:text-primary-700" disabled={loading}>
          Try Demo with sample data
        </button>
        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      </div>
    </div>
  );
}

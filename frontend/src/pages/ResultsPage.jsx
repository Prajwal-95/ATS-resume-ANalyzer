import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { analysisApi } from "../services/api";
import ScoreCircle from "../components/ScoreCircle";
import Badge from "../components/Badge";
import LoadingScreen from "../components/LoadingScreen";

const categoryLabels = {
  keyword_match: "Keyword Match",
  technical_skill: "Technical Skills",
  experience_relevance: "Experience Relevance",
  structure: "Structure",
  education: "Education",
  formatting: "Formatting",
};

export default function ResultsPage() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeSection, setActiveSection] = useState("overview");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await analysisApi.get(id);
        setAnalysis(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load analysis");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await analysisApi.downloadReport(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ats-report-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Failed to download report. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <LoadingScreen />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-6">
        <h2 className="text-2xl font-semibold text-gray-900">Unable to load analysis</h2>
        <p className="mt-2 text-gray-600">{error}</p>
      </div>
    );
  }

  const { total_score, scores, matched_keywords, missing_keywords, skill_matches, suggestions, quality_issues } = analysis;
  const scoreArray = Object.values(scores || {});

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "keywords", label: "Keywords" },
    { id: "skills", label: "Skills" },
    { id: "quality", label: "Quality" },
    { id: "suggestions", label: "Suggestions" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col items-center gap-8 md:flex-row md:items-start md:justify-between">
        <div className="text-center md:text-left">
          <h1 className="text-3xl font-bold text-gray-900">ATS Score</h1>
          <p className="mt-2 text-gray-600">
            {analysis.resume_filename || "Your resume"} vs {analysis.job_title || "the job description"}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <ScoreCircle score={total_score} />
          <button
            onClick={handleDownloadReport}
            disabled={downloading}
            className="btn-secondary flex items-center gap-2"
            aria-label="Download PDF report"
          >
            {downloading ? (
              "Generating..."
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export Report
              </>
            )}
          </button>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap gap-2 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSection(tab.id)}
            className={`rounded-t-lg border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeSection === tab.id
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-8">
        {activeSection === "overview" && (
          <OverviewSection
            scores={scoreArray}
            total={total_score}
            jobRelevance={analysis.job_relevance}
            disclaimer={analysis.disclaimer}
          />
        )}
        {activeSection === "keywords" && (
          <KeywordsSection matched={matched_keywords} missing={missing_keywords} />
        )}
        {activeSection === "skills" && <SkillsSection skills={skill_matches} />}
        {activeSection === "quality" && <QualitySection issues={quality_issues} />}
        {activeSection === "suggestions" && <SuggestionsSection suggestions={suggestions} />}
      </div>

      <div className="mt-12 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
        <strong>Disclaimer:</strong> {analysis.disclaimer}
      </div>
    </div>
  );
}

function OverviewSection({ scores, total, jobRelevance, disclaimer }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Category Scores</h3>
        <div className="space-y-4">
          {scores.map((s) => (
            <div key={s.category} className="card">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {categoryLabels[s.category] || s.category}
                </span>
                <span className="text-sm font-semibold text-gray-900">
                  {s.score} / {s.max_score}
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${(s.score / s.max_score) * 100}%`,
                    backgroundColor: s.score / s.max_score >= 0.8 ? "#10b981" : s.score / s.max_score >= 0.5 ? "#3b82f6" : "#f59e0b",
                  }}
                />
              </div>
              <div className="mt-2">
                <Badge status={s.score / s.max_score >= 0.8 ? "excellent" : s.score / s.max_score >= 0.5 ? "good" : s.score / s.max_score >= 0.25 ? "warning" : "problem"}>
                  {s.score / s.max_score >= 0.8 ? "Excellent" : s.score / s.max_score >= 0.5 ? "Good" : s.score / s.max_score >= 0.25 ? "Needs Improvement" : "Poor"}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Job Relevance</h3>
        <div className="card">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Overall Job Relevance</span>
            <span className="text-2xl font-bold text-primary-600">
              {jobRelevance ? Math.round(jobRelevance * 100) : 0}%
            </span>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-primary-600 transition-all duration-700"
              style={{ width: `${(jobRelevance || 0) * 100}%` }}
            />
          </div>
          <p className="mt-4 text-sm text-gray-500">
            This semantic similarity estimate measures how closely your resume content relates to
            the job description. It's an estimate, not a guaranteed ATS result.
          </p>
        </div>
        <div className="mt-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Summary</h3>
          <div className="card">
            <p className="text-3xl font-bold text-gray-900">{Math.round(total)} / 100</p>
            <p className="mt-2 text-gray-600">
              {total >= 80 ? "Great match! Your resume aligns well with this role." :
               total >= 60 ? "Good alignment. A few improvements could strengthen your match." :
               total >= 40 ? "Moderate match. Consider the suggestions to improve your resume." :
               "Your resume needs substantial improvement for this role."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


function KeywordsSection({ matched, missing }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900">Matched Keywords</h3>
        <p className="mt-1 text-sm text-gray-500">Keywords found in both the job description and your resume.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {(matched || []).length > 0 ? (
            matched.map((k) => (
              <span key={k.keyword} className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-sm text-emerald-700">
                {k.keyword} <span className="ml-1 text-emerald-500">✓</span>
              </span>
            ))
          ) : (
            <p className="text-sm text-gray-400">No matched keywords yet.</p>
          )}
        </div>
      </div>
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900">Missing Keywords</h3>
        <p className="mt-1 text-sm text-gray-500">Found in job description but not detected in your resume.</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {(missing || []).length > 0 ? (
            missing.map((k) => (
              <span key={k.keyword} className="inline-flex items-center rounded-full bg-red-50 px-3 py-1 text-sm text-red-700">
                {k.keyword}
              </span>
            ))
          ) : (
            <p className="text-sm text-gray-400">No missing keywords. Great job!</p>
          )}
        </div>
        {missing && missing.length > 0 && (
          <p className="mt-4 text-xs text-gray-500">
            These keywords appear in the job description but were not found in your resume. If you have
            genuine experience with any of them, consider mentioning them. Do not add skills you don't have.
          </p>
        )}
      </div>
    </div>
  );
}

function SkillsSection({ skills }) {
  const matched = (skills || []).filter((s) => s.match_type === "matched");
  const missing = (skills || []).filter((s) => s.match_type === "missing");
  const additional = (skills || []).filter((s) => s.match_type === "additional");

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="card">
        <h3 className="font-semibold text-gray-900">Required & Matched</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {matched.length > 0 ? matched.map((s) => (
            <Badge key={s.skill_name} status="matched">{s.skill_name}</Badge>
          )) : <p className="text-sm text-gray-400">No required skills matched.</p>}
        </div>
      </div>
      <div className="card">
        <h3 className="font-semibold text-gray-900">Missing Skills</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {missing.length > 0 ? missing.map((s) => (
            <Badge key={s.skill_name} status="missing">{s.skill_name}</Badge>
          )) : <p className="text-sm text-gray-400">No missing required skills.</p>}
        </div>
      </div>
      <div className="card">
        <h3 className="font-semibold text-gray-900">Additional Skills</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {additional.length > 0 ? additional.map((s) => (
            <Badge key={s.skill_name} status="additional">{s.skill_name}</Badge>
          )) : <p className="text-sm text-gray-400">No additional skills detected.</p>}
        </div>
      </div>
    </div>
  );
}


function QualitySection({ issues }) {
  const statusIcon = { good: "✓", warning: "⚠", problem: "✗" };
  const statusColor = { good: "text-emerald-600", warning: "text-amber-600", problem: "text-red-600" };

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900">Resume Quality Analysis</h3>
      <div className="mt-4 space-y-3">
        {(issues || []).map((issue, i) => (
          <div key={i} className="flex items-start gap-3 rounded-lg bg-gray-50 p-3">
            <span className={`mt-0.5 text-lg ${statusColor[issue.status] || "text-gray-500"}`}>
              {statusIcon[issue.status] || "•"}
            </span>
            <div>
              <p className="text-sm font-medium text-gray-800">{issue.label}</p>
              <p className="text-sm text-gray-600">{issue.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SuggestionsSection({ suggestions }) {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900">Improvement Suggestions</h3>
      <div className="mt-4 space-y-4">
        {(suggestions || []).map((sug, i) => (
          <div key={i} className="flex items-start gap-3 rounded-lg border border-gray-100 p-4">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm text-primary-700">
              {i + 1}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800">{sug.category}</p>
              <p className="mt-1 text-sm text-gray-600">{sug.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


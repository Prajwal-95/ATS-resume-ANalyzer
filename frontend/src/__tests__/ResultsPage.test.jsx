import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ResultsPage from "../pages/ResultsPage";
import { analysisApi } from "../services/api";

vi.mock("../services/api", () => ({
  analysisApi: {
    get: vi.fn(),
    history: vi.fn(),
    delete: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

const mockAnalysis = {
  id: 1,
  resume_filename: "test-resume.pdf",
  job_title: "Software Engineer",
  total_score: 75,
  scores: [
    { category: "keyword_match", score: 22, max_score: 30, details: {} },
    { category: "technical_skill", score: 18, max_score: 25, details: {} },
    { category: "experience_relevance", score: 15, max_score: 20, details: {} },
    { category: "structure", score: 8, max_score: 10, details: {} },
    { category: "education", score: 5, max_score: 5, details: {} },
    { category: "formatting", score: 7, max_score: 10, details: {} },
  ],
  matched_keywords: [{ keyword: "Python", confidence: 1.0 }],
  missing_keywords: [{ keyword: "Docker", importance: "high" }],
  skill_matches: [
    { skill_name: "Python", match_type: "matched", is_required: true },
    { skill_name: "Docker", match_type: "missing", is_required: true },
  ],
  suggestions: [{ category: "keyword", message: "Add Docker experience", priority: "high" }],
  quality_issues: [
    { category: "email", label: "Email address", message: "Email found.", status: "good" },
  ],
  structured_resume: { name: "John Doe", email: "john@example.com" },
  semantic_similarity: 0.75,
  job_relevance: 0.75,
  disclaimer: "This is an estimate.",
  created_at: "2024-01-01T00:00:00Z",
};

function renderResults() {
  return render(
    <MemoryRouter initialEntries={["/results/1"]}>
      <Routes>
        <Route path="/results/:id" element={<ResultsPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ResultsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders analysis data", async () => {
    analysisApi.get.mockResolvedValue(mockAnalysis);
    renderResults();

    // Wait for the score circle to appear (confirms data loaded)
    expect(await screen.findByText(/export report/i)).toBeInTheDocument();
    expect(screen.getByText(/test-resume\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/software engineer/i)).toBeInTheDocument();
  });

  it("renders category scores", async () => {
    analysisApi.get.mockResolvedValue(mockAnalysis);
    renderResults();

    expect(await screen.findByText(/keyword match/i)).toBeInTheDocument();
    expect(screen.getByText(/22/i)).toBeInTheDocument();
  });

  it("renders tabs", async () => {
    analysisApi.get.mockResolvedValue(mockAnalysis);
    renderResults();

    expect(await screen.findByRole("button", { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /keywords/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /skills/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /quality/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /suggestions/i })).toBeInTheDocument();
  });

  it("shows matched and missing keywords", async () => {
    analysisApi.get.mockResolvedValue(mockAnalysis);
    renderResults();

    await userEvent.click(await screen.findByRole("button", { name: /keywords/i }));
    expect(await screen.findByText(/python/i)).toBeInTheDocument();
    expect(screen.getByText(/docker/i)).toBeInTheDocument();
  });

  it("shows export report button", async () => {
    analysisApi.get.mockResolvedValue(mockAnalysis);
    renderResults();

    expect(await screen.findByRole("button", { name: /download pdf report/i })).toBeInTheDocument();
  });

  it("handles API error", async () => {
    analysisApi.get.mockRejectedValue(new Error("Network error"));
    renderResults();

    expect(await screen.findByText(/unable to load analysis/i)).toBeInTheDocument();
  });
});

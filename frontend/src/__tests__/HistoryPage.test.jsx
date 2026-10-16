import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import HistoryPage from "../pages/HistoryPage";
import { analysisApi } from "../services/api";
import { AuthProvider } from "../context/AuthContext";

vi.mock("../services/api", () => ({
  analysisApi: {
    get: vi.fn(),
    history: vi.fn(),
    delete: vi.fn(),
    downloadReport: vi.fn(),
  },
}));

vi.mock("../context/AuthContext", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useAuth: () => ({
      user: { id: 1, username: "testuser", email: "test@example.com" },
      token: "mock-token",
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    }),
  };
});

const mockHistory = [
  { id: 1, resume_filename: "resume1.pdf", job_title: "Software Engineer", total_score: 85, created_at: "2024-01-01T00:00:00Z" },
  { id: 2, resume_filename: "resume2.pdf", job_title: "Data Scientist", total_score: 72, created_at: "2024-01-02T00:00:00Z" },
];

function renderHistory() {
  return render(
    <MemoryRouter initialEntries={["/history"]}>
      <AuthProvider>
        <Routes>
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("HistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    // Mock window.confirm for jsdom
    window.confirm = vi.fn(() => true);
  });

  it("renders empty state", async () => {
    analysisApi.history.mockResolvedValue([]);
    renderHistory();

    expect(await screen.findByText(/no analyses yet/i)).toBeInTheDocument();
  });

  it("renders analysis list", async () => {
    analysisApi.history.mockResolvedValue(mockHistory);
    renderHistory();

    expect(await screen.findByText(/resume1\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/resume2\.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/software engineer/i)).toBeInTheDocument();
  });

  it("deletes an analysis", async () => {
    analysisApi.history.mockResolvedValue(mockHistory);
    analysisApi.delete.mockResolvedValue({});
    window.confirm = vi.fn(() => true);

    renderHistory();

    const deleteButtons = await screen.findAllByRole("button", { name: /delete analysis/i });
    await userEvent.click(deleteButtons[0]);

    expect(analysisApi.delete).toHaveBeenCalledWith(1);
  });

  it("handles API error", async () => {
    analysisApi.history.mockRejectedValue(new Error("Network error"));
    renderHistory();

    expect(await screen.findByText(/failed to load history/i)).toBeInTheDocument();
  });
});

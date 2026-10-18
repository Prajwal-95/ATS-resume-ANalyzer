import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import UploadPage from "../pages/UploadPage";
import { AuthProvider } from "../context/AuthContext";
import { resumeApi } from "../services/api";
import { demoResume, demoJobDescription } from "../utils/demoData";

// Mock the API
vi.mock("../services/api", () => ({
  resumeApi: {
    demo: vi.fn().mockResolvedValue({ id: 1 }),
    analyze: vi.fn().mockResolvedValue({ id: 1 }),
  },
}));

function renderWithProviders(ui) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
}

function renderWithDemoRoutes(initialEntry) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <Routes>
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/results/:id" element={<div data-testid="results-view" />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("UploadPage", () => {
  it("renders upload form", () => {
    renderWithProviders(<UploadPage />);
    expect(screen.getByText("Analyze Your Resume")).toBeInTheDocument();
    expect(screen.getByText("1. Upload Resume")).toBeInTheDocument();
    expect(screen.getByText("2. Paste Job Description")).toBeInTheDocument();
  });

  it("shows error when no file selected", async () => {
    renderWithProviders(<UploadPage />);
    const button = screen.getByRole("button", { name: /analyze resume/i });
    await userEvent.click(button);
    expect(await screen.findByRole("alert")).toHaveTextContent("Please upload a resume file");
  });

  it("shows error when job description is empty", async () => {
    renderWithProviders(<UploadPage />);
    // Create a mock file
    const file = new File(["dummy content"], "resume.pdf", { type: "application/pdf" });
    const input = screen.getByLabelText("Choose resume file");
    await userEvent.upload(input, file);

    const button = screen.getByRole("button", { name: /analyze resume/i });
    await userEvent.click(button);
    expect(await screen.findByRole("alert")).toHaveTextContent("Please paste a job description");
  });

  it("shows demo button", () => {
    renderWithProviders(<UploadPage />);
    expect(screen.getByRole("button", { name: /try demo/i })).toBeInTheDocument();
  });

  it("renders drag and drop area", () => {
    renderWithProviders(<UploadPage />);
    expect(screen.getByRole("button", { name: /upload resume file/i })).toBeInTheDocument();
  });

  it("renders job description textarea", () => {
    renderWithProviders(<UploadPage />);
    expect(screen.getByLabelText("Job description")).toBeInTheDocument();
  });
});

describe("UploadPage demo interaction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls the demo API with sample data and navigates to results on button click", async () => {
    renderWithDemoRoutes("/upload");

    await userEvent.click(screen.getByRole("button", { name: /try demo with sample data/i }));

    expect(resumeApi.demo).toHaveBeenCalledWith(demoResume, demoJobDescription);
    expect(await screen.findByTestId("results-view")).toBeInTheDocument();
  });

  it("auto-triggers the demo when navigating to /upload?demo=1", async () => {
    renderWithDemoRoutes("/upload?demo=1");

    expect(resumeApi.demo).toHaveBeenCalledWith(demoResume, demoJobDescription);
    expect(await screen.findByTestId("results-view")).toBeInTheDocument();
  });

  it("shows a backend-unavailable error when the demo request fails with no response", async () => {
    resumeApi.demo.mockRejectedValue(new Error("Network error"));
    renderWithDemoRoutes("/upload");

    await userEvent.click(screen.getByRole("button", { name: /try demo/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/backend is unavailable/i);
  });

  it("shows a rate-limited message when the demo request gets a 429", async () => {
    resumeApi.demo.mockRejectedValue({ response: { status: 429, data: { detail: "Rate limit exceeded" } } });
    renderWithDemoRoutes("/upload");

    await userEvent.click(screen.getByRole("button", { name: /try demo/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/rate-limited/i);
  });

  it("shows a server-error message when the demo request gets a 500", async () => {
    resumeApi.demo.mockRejectedValue({ response: { status: 500, data: { detail: "Analysis failed" } } });
    renderWithDemoRoutes("/upload");

    await userEvent.click(screen.getByRole("button", { name: /try demo/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/encountered an error/i);
  });

  it("shows the backend detail message for a 400 demo response", async () => {
    resumeApi.demo.mockRejectedValue({ response: { status: 400, data: { detail: "Resume text cannot be empty" } } });
    renderWithDemoRoutes("/upload");

    await userEvent.click(screen.getByRole("button", { name: /try demo/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Resume text cannot be empty");
  });
});

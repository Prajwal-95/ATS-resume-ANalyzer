import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import UploadPage from "../pages/UploadPage";
import { AuthProvider } from "../context/AuthContext";

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

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Link } from "react-router-dom";
import LampLoginPage from "../pages/LampLoginPage";
import LampRegisterPage from "../pages/LampRegisterPage";
import { AuthProvider } from "../context/AuthContext";
import { authApi } from "../services/api";

vi.mock("../services/api", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
  },
}));

function renderRoute(element, initialEntry) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <Routes>
          <Route path={initialEntry} element={element} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("Login route rendering (regression)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the animated lamp login page on direct navigation to /login", () => {
    renderRoute(<LampLoginPage />, "/login");

    expect(screen.getByText(/pull the string to turn on/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByText(/blank/i)).not.toBeInTheDocument();
  });

  it("renders the animated lamp register page on direct navigation to /register", () => {
    renderRoute(<LampRegisterPage />, "/register");

    expect(screen.getByText(/pull the string to turn on/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign up/i })).toBeInTheDocument();
  });

  it("navigates to the lamp login page client-side without a hard refresh", async () => {
    function HomeLink() {
      return (
        <div>
          <Link to="/login">Log in</Link>
        </div>
      );
    }
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<HomeLink />} />
            <Route path="/login" element={<LampLoginPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await userEvent.click(screen.getByRole("link", { name: /log in/i }));
    expect(screen.getByText(/pull the string to turn on/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});

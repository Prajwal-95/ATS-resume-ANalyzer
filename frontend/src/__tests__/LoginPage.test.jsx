import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route, Link } from "react-router-dom";
import LampLoginPage from "../pages/LampLoginPage";
import LampRegisterPage from "../pages/LampRegisterPage";
import { AuthProvider } from "../context/AuthContext";
import { LampProvider } from "../context/LampContext";
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
        <LampProvider>
          <Routes>
            <Route path={initialEntry} element={element} />
          </Routes>
        </LampProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

function renderBothRoutes(initialEntry) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <LampProvider>
          <Routes>
            <Route path="/login" element={<LampLoginPage />} />
            <Route path="/register" element={<LampRegisterPage />} />
          </Routes>
        </LampProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

function getRoom(container) {
  return container.querySelector(".lamp-auth-room");
}

function activateLamp(container) {
  const handle = container.querySelector("#stringHandle");
  act(() => {
    fireEvent.keyDown(handle, { key: "Enter" });
  });
}

describe("Login route rendering (regression)", () => {
  beforeEach(() => {
    sessionStorage.clear();
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
          <LampProvider>
            <Routes>
              <Route path="/" element={<HomeLink />} />
              <Route path="/login" element={<LampLoginPage />} />
            </Routes>
          </LampProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await userEvent.click(screen.getByRole("link", { name: /log in/i }));
    expect(screen.getByText(/pull the string to turn on/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});

describe("Lamp activation reveals the login form", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("starts with the lamp off (no on class on the auth room)", () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");
    const room = getRoom(container);

    expect(room).not.toHaveClass("on");
  });

  it("applies the on class to the room after activating the lamp via keyboard", () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");
    const room = getRoom(container);

    expect(room).not.toHaveClass("on");

    activateLamp(container);

    expect(room).toHaveClass("on");
  });

  it("toggles the lamp off again after a second activation", () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");
    const room = getRoom(container);

    activateLamp(container);
    expect(room).toHaveClass("on");

    activateLamp(container);
    expect(room).not.toHaveClass("on");
  });

  it("exposes email and password fields that accept input after lamp activation", async () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");

    const emailInput = screen.getByPlaceholderText(/email address/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    activateLamp(container);

    await userEvent.type(emailInput, "user@example.com");
    await userEvent.type(passwordInput, "secret");

    expect(emailInput).toHaveValue("user@example.com");
    expect(passwordInput).toHaveValue("secret");
  });

  it("keeps the sign-in button present and usable after lamp activation", async () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");

    const submit = screen.getByRole("button", { name: /sign in/i });

    activateLamp(container);

    expect(submit).not.toBeDisabled();
  });

  it("reveals the registration form after lamp activation on the register route", () => {
    const { container } = renderRoute(<LampRegisterPage />, "/register");
    const room = getRoom(container);

    expect(room).not.toHaveClass("on");

    activateLamp(container);

    expect(room).toHaveClass("on");
    expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
  });

  it("navigates from login to registration via the link without reactivating the lamp", async () => {
    renderBothRoutes("/login");

    activateLamp(document.body);
    expect(document.querySelector(".lamp-auth-room")).toHaveClass("on");

    await userEvent.click(screen.getByRole("link", { name: /sign up/i }));

    expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
  });
});

describe("Lamp state persists across route navigation", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("keeps the lamp ON when navigating from /login to /register", async () => {
    const { container } = renderBothRoutes("/login");

    activateLamp(container);
    expect(getRoom(container)).toHaveClass("on");

    await userEvent.click(screen.getByRole("link", { name: /sign up/i }));

    const registerRoom = document.querySelector(".lamp-auth-room");
    expect(registerRoom).toHaveClass("on");
  });

  it("keeps the lamp ON when navigating back from /register to /login", async () => {
    const { container } = renderBothRoutes("/login");

    activateLamp(container);
    expect(getRoom(container)).toHaveClass("on");

    await userEvent.click(screen.getByRole("link", { name: /sign up/i }));
    expect(document.querySelector(".lamp-auth-room")).toHaveClass("on");

    await userEvent.click(screen.getByRole("link", { name: /log in/i }));

    const loginRoom = document.querySelector(".lamp-auth-room");
    expect(loginRoom).toHaveClass("on");
  });

  it("turns the lamp OFF via the pull-string interaction", async () => {
    const { container } = renderBothRoutes("/login");

    activateLamp(container);
    expect(getRoom(container)).toHaveClass("on");

    activateLamp(container);
    expect(getRoom(container)).not.toHaveClass("on");
  });

  it("restores the lamp ON state from sessionStorage on page refresh", () => {
    sessionStorage.setItem("lamp_auth_on", "true");

    const { container } = renderRoute(<LampLoginPage />, "/login");
    const room = getRoom(container);

    expect(room).toHaveClass("on");
  });

  it("restores the lamp OFF state from sessionStorage on page refresh", () => {
    sessionStorage.setItem("lamp_auth_on", "false");

    const { container } = renderRoute(<LampLoginPage />, "/login");
    const room = getRoom(container);

    expect(room).not.toHaveClass("on");
  });

  it("does not persist authentication tokens or passwords in sessionStorage", () => {
    const { container } = renderRoute(<LampLoginPage />, "/login");
    activateLamp(container);

    const keys = Object.keys(sessionStorage).filter(
      (k) => k !== "lamp_auth_on"
    );
    expect(keys.length).toBe(0);
  });
});

describe("Social login placeholders show Coming Soon", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("displays Coming Soon under Google on the login form", () => {
    renderRoute(<LampLoginPage />, "/login");

    const comingSoonLabels = screen.getAllByText(/coming soon/i);
    expect(comingSoonLabels.length).toBeGreaterThanOrEqual(1);

    const googleButton = screen.getByRole("button", { name: /Google/i });
    const googleSection = googleButton.closest(".social-option");
    expect(googleSection).toBeInTheDocument();
    expect(googleSection.querySelector(".coming-soon")).toHaveTextContent("Coming Soon");
  });

  it("displays Coming Soon under GitHub on the login form", () => {
    renderRoute(<LampLoginPage />, "/login");

    const githubButton = screen.getByRole("button", { name: /GitHub/i });
    const githubSection = githubButton.closest(".social-option");
    expect(githubSection).toBeInTheDocument();
    expect(githubSection.querySelector(".coming-soon")).toHaveTextContent("Coming Soon");
  });

  it("displays Coming Soon under Google on the register form", () => {
    renderRoute(<LampRegisterPage />, "/register");

    const googleButton = screen.getByRole("button", { name: /Google/i });
    const googleSection = googleButton.closest(".social-option");
    expect(googleSection).toBeInTheDocument();
    expect(googleSection.querySelector(".coming-soon")).toHaveTextContent("Coming Soon");
  });

  it("displays Coming Soon under GitHub on the register form", () => {
    renderRoute(<LampRegisterPage />, "/register");

    const githubButton = screen.getByRole("button", { name: /GitHub/i });
    const githubSection = githubButton.closest(".social-option");
    expect(githubSection).toBeInTheDocument();
    expect(githubSection.querySelector(".coming-soon")).toHaveTextContent("Coming Soon");
  });

  it("keeps social buttons disabled as nonfunctional placeholders", () => {
    renderRoute(<LampLoginPage />, "/login");

    const googleButton = screen.getByRole("button", { name: /Google/i });
    const githubButton = screen.getByRole("button", { name: /GitHub/i });

    expect(googleButton).toBeDisabled();
    expect(githubButton).toBeDisabled();
  });
});
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "../context/AuthContext";
import { authApi } from "../services/api";

vi.mock("../services/api", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
  },
}));

function TestComponent() {
  const { user, token, login, register, logout, loading } = useAuth();
  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? user.username : "none"}</div>
      <div data-testid="token">{token ? "has-token" : "no-token"}</div>
      <button onClick={() => login("test@test.com", "password123")}>Login</button>
      <button onClick={() => register("test@test.com", "testuser", "password123")}>Register</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("starts with no user and not loading", () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );
    expect(screen.getByTestId("loading")).toHaveTextContent("false");
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(screen.getByTestId("token")).toHaveTextContent("no-token");
  });

  it("logs in and stores token", async () => {
    authApi.login.mockResolvedValue({ access_token: "test-token-123" });
    authApi.me.mockResolvedValue({ id: 1, username: "testuser", email: "test@test.com" });

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await userEvent.click(screen.getByText("Login"));

    expect(localStorage.getItem("ats_token")).toBe("test-token-123");
    expect(screen.getByTestId("user")).toHaveTextContent("testuser");
  });

  it("logs out and clears storage", async () => {
    localStorage.setItem("ats_token", "old-token");
    localStorage.setItem("ats_user", JSON.stringify({ username: "old" }));

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await userEvent.click(screen.getByText("Logout"));

    expect(localStorage.getItem("ats_token")).toBeNull();
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });
});

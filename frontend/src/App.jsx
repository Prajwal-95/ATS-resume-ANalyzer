import { Routes, Route, useLocation } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import UploadPage from "./pages/UploadPage";
import ResultsPage from "./pages/ResultsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import HistoryPage from "./pages/HistoryPage";
import LampLoginPage from "./pages/LampLoginPage";
import LampRegisterPage from "./pages/LampRegisterPage";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import { AuthProvider } from "./context/AuthContext";

function AppContent() {
  const location = useLocation();
  const isAuthRoute = location.pathname === "/login" || location.pathname === "/register" || location.pathname === "/lamp/login" || location.pathname === "/lamp/register";

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      {!isAuthRoute && <Navbar />}
      <main className="flex-1" id="main-content">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/results/:id" element={<ResultsPage />} />
          <Route path="/login" element={<LampLoginPage />} />
          <Route path="/register" element={<LampRegisterPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
      {!isAuthRoute && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

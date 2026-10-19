import axios from "axios";

// Backend API URL.
// - Development: falls back to the local backend when VITE_API_URL is unset.
// - Production build (same-origin): defaults to empty string so all axios
//   requests go to the current origin (e.g., /auth/login instead of
//   http://localhost:8000/auth/login). This works because the FastAPI
//   server serves both the React SPA and the API from the same origin.
// - If VITE_API_URL is explicitly set (e.g., to a separate backend URL),
//   that value takes precedence.
const BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? "" : "http://localhost:8000");

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to all requests if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ats_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 by clearing token
    if (error.response?.status === 401) {
      localStorage.removeItem("ats_token");
      localStorage.removeItem("ats_user");
    }
    return Promise.reject(error);
  }
);

// ── Auth ──
export const authApi = {
  register: (email, username, password) =>
    api.post("/auth/register", { email, username, password }).then((r) => r.data),
  login: (email, password) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  me: (token) =>
    api.get("/auth/me", { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.data),
  verifyEmail: (token) =>
    api.post("/auth/verify-email", { token }).then((r) => r.data),
  resendVerification: (email) =>
    api.post("/auth/resend-verification", { email }).then((r) => r.data),
  forgotPassword: (email) =>
    api.post("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (token, newPassword) =>
    api.post("/auth/reset-password", { token, new_password: newPassword }).then((r) => r.data),
};

// ── Resume / Analysis ──
const toFormData = (file, jobDescription) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("job_description", jobDescription);
  return formData;
};

export const resumeApi = {
  analyze: (file, jobDescription, onUploadProgress) =>
    api
      .post("/analysis/analyze", toFormData(file, jobDescription), {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: onUploadProgress || undefined,
      })
      .then((r) => r.data),

  demo: (resumeText, jobDescription) =>
    api
      .post("/analysis/demo", { resume_text: resumeText, job_description: jobDescription })
      .then((r) => r.data),

  upload: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api
      .post("/resume/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};

export const analysisApi = {
  history: () => api.get("/analysis/history").then((r) => r.data),
  get: (id) => api.get(`/analysis/${id}`).then((r) => r.data),
  delete: (id) => api.delete(`/analysis/${id}`),
  downloadReport: (id) =>
    api.get(`/analysis/${id}/report`, { responseType: "blob" }).then((r) => r.data),
};

export default api;

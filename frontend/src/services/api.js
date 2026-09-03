import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
};

// ── Resume / Analysis ──
const toFormData = (file, jobDescription) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("job_description", jobDescription);
  return formData;
};

export const resumeApi = {
  analyze: (file, jobDescription) =>
    api
      .post("/analysis/analyze", toFormData(file, jobDescription), {
        headers: { "Content-Type": "multipart/form-data" },
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
};

export default api;

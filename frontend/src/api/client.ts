import axios from 'axios';

// Use Vite proxy in dev (/api → http://localhost:8000)
// or VITE_API_URL env var in production
const API_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : '/api';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000, // 60s for LLM calls
});

// JWT interceptor — attach token from localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('ks_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global error handler
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and do a hard redirect to break any React Router loops
      if (!window.location.pathname.startsWith('/login')) {
        localStorage.removeItem('ks_token');
        localStorage.removeItem('ks_user');
        window.location.replace('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/login', { username, password }),
  getMe: () => api.get('/me'),
};

export const reportsAPI = {
  list: (status) => api.get('/reports', { params: status ? { status } : {} }),
  getLocations: () => api.get('/reports/locations'),
  get: (id) => api.get(`/reports/${id}`),
  create: (formData) => api.post('/reports', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  verify: (id, reason) => api.patch(`/reports/${id}/verify`, { reason }),
  updateStatus: (id, status, reason) => api.patch(`/reports/${id}/status`, { status, reason }),
  getHistory: (id) => api.get(`/reports/${id}/history`),
};

export const tokensAPI = {
  getBalance: () => api.get('/tokens/balance'),
  getHistory: () => api.get('/tokens/history'),
};

export const rewardsAPI = {
  list: () => api.get('/rewards'),
  redeem: (id) => api.post(`/rewards/${id}/redeem`),
};

export const dashboardAPI = {
  get: () => api.get('/dashboard'),
};

export default api;

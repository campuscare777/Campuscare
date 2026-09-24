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
  /** List complaints with optional status, hostel_type, and category filters. */
  list: (status, hostelType, category, foodRelated) => {
    const params = {};
    if (status)      params.status      = status;
    if (hostelType)  params.hostel_type = hostelType;
    if (category)    params.category    = category;
    if (foodRelated !== undefined && foodRelated !== null) params.food_related = foodRelated;
    return api.get('/reports', { params });
  },
  /** Return hostel types, per-hostel blocks, and complaint categories for dropdowns. */
  getHostelConfig: () => api.get('/reports/hostel-config'),
  /** Backward-compat: flat locations list */
  getLocations: () => api.get('/reports/locations'),
  get: (id) => api.get(`/reports/${id}`),
  create: (formData) => api.post('/reports', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  verify: (id, reason) => api.patch(`/reports/${id}/verify`, { reason }),
  forwardToAdmin: (id, reason) => api.patch(`/reports/${id}/forward-to-admin`, { reason }),
  adminVerify: (id, reason) => api.patch(`/reports/${id}/admin-verify`, { reason }),
  completeWork: (id, reason) => api.patch(`/reports/${id}/complete-work`, { reason }),
  adminResolve: (id, reason) => api.patch(`/reports/${id}/admin-resolve`, { reason }),
  reject: (id, reason) => api.patch(`/reports/${id}/reject`, { reason }),
  assign: (id, assigned_team) => api.patch(`/reports/${id}/assign`, { assigned_team }),
  updateStatus: (id, status, reason) => api.patch(`/reports/${id}/status`, { status, reason }),
  getHistory: (id) => api.get(`/reports/${id}/history`),
};

export const tokensAPI = {
  getBalance: () => api.get('/tokens/balance'),
  getHistory: () => api.get('/tokens/history'),
};

export const rewardsAPI = {
  /** List reward catalog, optionally filter by category: "Canteen" | "Laundry" | "Hostel Stores" */
  list: (category) => api.get('/rewards', { params: category ? { category } : {} }),
  redeem: (id) => api.post(`/rewards/${id}/redeem`),
  /** Staff: look up a voucher reference */
  lookupRedemption: (voucherRef) => api.get(`/redemptions/${voucherRef}`),
  /** Staff: mark a voucher as fulfilled */
  fulfillRedemption: (voucherRef) => api.patch(`/redemptions/${voucherRef}/fulfill`),

  // Admin / Warden reward management (HOSTELCARE-F003-UI-004)
  /** Admin: list ALL rewards including inactive */
  adminList: () => api.get('/admin/rewards'),
  /** Admin: create a new reward */
  adminCreate: (data) => api.post('/admin/rewards', data),
  /** Admin: update a reward's details, token cost, or availability */
  adminUpdate: (id, data) => api.put(`/admin/rewards/${id}`, data),
  /** Admin: soft-delete (deactivate) a reward */
  adminDelete: (id) => api.delete(`/admin/rewards/${id}`),
};

export const dashboardAPI = {
  get: () => api.get('/dashboard'),
};

export default api;

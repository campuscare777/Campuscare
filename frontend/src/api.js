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
  /** List complaints with optional filters per HOSTELCARE-CROSS-003. */
  list: (params = {}) => {
    const p = {};
    if (params.status)        p.status        = params.status;
    if (params.hostelType)    p.hostel_type   = params.hostelType;
    if (params.category)      p.category      = params.category;
    if (params.block)         p.block         = params.block;
    if (params.floor)         p.floor         = params.floor;
    if (params.assignedTeam)  p.assigned_team = params.assignedTeam;
    if (params.dateFrom)      p.date_from     = params.dateFrom;
    if (params.dateTo)        p.date_to       = params.dateTo;
    if (params.reporterId)    p.reporter_id   = params.reporterId;
    if (params.foodRelated !== undefined && params.foodRelated !== null) p.food_related = params.foodRelated;
    return api.get('/reports', { params: p });
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
export const lostAndFoundAPI = {
  /** List lost & found items with optional filters (category, hostelType, reportType, status, hideClosed, myReports, search). */
  list: (params) => api.get('/lost-and-found', { params }),
  /** Retrieve a single item report by ID. */
  get: (id) => api.get(`/lost-and-found/${id}`),
  /** Create a new lost or found report (supports multipart/form-data or JSON). */
  create: (formData) =>
    api.post('/lost-and-found', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  /** Resident submits a claim request for an item (AC1, AC2). */
  claim: (id, data) => api.post(`/lost-and-found/${id}/claim`, data),
  /** List item claims with optional filters (item_report_id, status, my_claims). */
  listClaims: (params) => api.get('/lost-and-found/claims', { params }),
  /** Retrieve claims for a specific item report. */
  getItemClaims: (id) => api.get(`/lost-and-found/${id}/claims`),
  /** Staff reviews and approves a claim (AC3). */
  verifyClaim: (claimId, data) => api.post(`/lost-and-found/claims/${claimId}/verify`, data),
  /** Staff rejects a claim with mandatory reason (AC4). */
  rejectClaim: (claimId, data) => api.post(`/lost-and-found/claims/${claimId}/reject`, data),
  /** Staff confirms item handover to verified claimant (AC5). */
  handoverItem: (claimId, data) => api.post(`/lost-and-found/claims/${claimId}/handover`, data),
  /** Staff / Admin updates status of a lost/found report. */
  updateStatus: (id, data) => api.patch(`/lost-and-found/${id}/status`, data),
  /** Get audit history of status changes. */
  getHistory: (id) => api.get(`/lost-and-found/${id}/history`),
};

export const notificationsAPI = {
  /** List notifications with optional unread_only, limit, offset params */
  list: (params) => api.get('/notifications', { params }),
  /** Get count of unread notifications */
  getUnreadCount: () => api.get('/notifications/unread-count'),
  /** Mark single notification as read */
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  /** Mark all notifications as read */
  markAllRead: () => api.post('/notifications/mark-all-read'),
};

export default api;

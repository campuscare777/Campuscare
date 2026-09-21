import { useState, useEffect } from 'react';
import {
  CheckCircle, Clock, AlertCircle, ShieldCheck, History,
  ChevronRight, Filter, RefreshCw, X, Coins, Bell, Send, ArrowRight
} from 'lucide-react';
import { reportsAPI } from './api';
import { useAuth } from './AuthContext';

// Toast notification component shown when actions occur
function ToastNotification({ toast, onDismiss }) {
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onDismiss, 5000);
    return () => clearTimeout(t);
  }, [toast]);
  if (!toast) return null;
  return (
    <div
      id="staff-toast-notification"
      style={{
        position: 'fixed', bottom: 32, right: 32, zIndex: 9999,
        background: toast.type === 'resolved' ? 'linear-gradient(135deg,#059669,#047857)' :
                    toast.type === 'verified' ? 'linear-gradient(135deg,#7c3aed,#6d28d9)' :
                    toast.type === 'tokens'   ? 'linear-gradient(135deg,#059669,#047857)' :
                    'linear-gradient(135deg,#dc2626,#b91c1c)',
        color: '#fff', borderRadius: 16, padding: '18px 24px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.22)', minWidth: 320, maxWidth: 420,
        display: 'flex', alignItems: 'flex-start', gap: 14,
        animation: 'slideInRight 0.3s ease',
      }}
    >
      <div style={{ marginTop: 2 }}>
        {toast.type === 'tokens' ? <Coins size={22} /> :
         toast.type === 'resolved' ? <CheckCircle size={22} /> :
         toast.type === 'verified' ? <ShieldCheck size={22} /> :
         <AlertCircle size={22} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 4 }}>{toast.title}</div>
        <div style={{ fontSize: 13, opacity: 0.92, lineHeight: 1.5 }}>{toast.message}</div>
      </div>
      <button onClick={onDismiss} style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#fff', cursor: 'pointer', borderRadius: 8, padding: 4, marginTop: -2 }}>
        <X size={16} />
      </button>
    </div>
  );
}

export default function StaffReportsQueue({ onReportUpdated }) {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [hostelFilter, setHostelFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [reasonInput, setReasonInput] = useState('');
  const [activeReasonId, setActiveReasonId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [toast, setToast] = useState(null);

  const isFoodStaff = user?.role === 'food_staff';
  const isWarden = user?.role === 'warden' || user?.role === 'maintenance';
  const isAdmin = user?.role === 'admin';

  const loadReports = () => {
    setLoading(true);
    reportsAPI
      .list(filter || undefined, hostelFilter || undefined, categoryFilter || undefined)
      .then((res) => {
        setReports(res.data.reports || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load hostel complaint queue:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadReports();
  }, [filter, hostelFilter, categoryFilter]);

  // Step 2: Food Staff / Warden verifies and forwards to Admin
  const handleForwardToAdmin = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.forwardToAdmin(reportId, reasonInput || undefined);
      setReasonInput('');
      setActiveReasonId(null);
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
      setToast({
        type: 'verified',
        title: 'Verified & Forwarded to Admin',
        message: `Complaint #${reportId} verified and forwarded to Admin for approval and token generation.`,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to forward complaint to Admin');
    } finally {
      setActionLoading(null);
    }
  };

  // Step 3: Admin verifies forwarded complaint & generates Green Tokens for student
  const handleAdminVerify = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.adminVerify(reportId, reasonInput || undefined);
      setReasonInput('');
      setActiveReasonId(null);
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
      setToast({
        type: 'tokens',
        title: 'Admin Verified & Tokens Awarded! 🪙',
        message: `Complaint #${reportId} verified! 10 Green Tokens generated for student. Returned to staff for on-site resolution.`,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to verify complaint as Admin');
    } finally {
      setActionLoading(null);
    }
  };

  // Step 4: Staff solves issue on-site and reports back to Admin
  const handleCompleteWork = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.completeWork(reportId, reasonInput || undefined);
      setReasonInput('');
      setActiveReasonId(null);
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
      setToast({
        type: 'verified',
        title: 'Work Completed & Reported to Admin',
        message: `Complaint #${reportId} marked completed on-site and reported to Admin for final closure.`,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to report work completion');
    } finally {
      setActionLoading(null);
    }
  };

  // Step 5: Admin confirms final completion and closes complaint
  const handleAdminResolve = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.adminResolve(reportId, reasonInput || undefined);
      setReasonInput('');
      setActiveReasonId(null);
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
      setToast({
        type: 'resolved',
        title: 'Complaint Resolved & Closed ✓',
        message: `Complaint #${reportId} has been confirmed resolved and closed. Resident notified.`,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to resolve complaint as Admin');
    } finally {
      setActionLoading(null);
    }
  };

  // Reject complaint
  const handleReject = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.reject(reportId, reasonInput || 'Complaint marked invalid by staff');
      setReasonInput('');
      setActiveReasonId(null);
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
      setToast({
        type: 'rejected',
        title: 'Complaint Rejected',
        message: `Complaint #${reportId} marked as rejected.`,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to reject complaint');
    } finally {
      setActionLoading(null);
    }
  };

  const openHistory = async (report) => {
    setSelectedReport(report);
    setHistoryLoading(true);
    setErrorMessage('');
    try {
      const res = await reportsAPI.getHistory(report.id);
      setHistory(res.data || []);
    } catch (err) {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const statusStyles = (s) => ({
    'Submitted':               { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
    'Under Review':            { bg: '#fef9c3', text: '#a16207', border: '#fde68a' },
    'Verified by Food Staff':  { bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
    'Verified by Warden':      { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe' },
    'Verified':                { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe' },
    'Admin Verified':          { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' },
    'In Progress':             { bg: '#fffbeb', text: '#d97706', border: '#fde68a' },
    'Work Completed':          { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
    'Resolved':                { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' },
    'Rejected':                { bg: '#fef2f2', text: '#dc2626', border: '#fecaca' },
  }[s] || { bg: '#f8fafc', text: '#64748b', border: '#e2e8f0' });

  // Custom role banner header info
  const headerInfo = isFoodStaff ? {
    title: 'Food & Mess Complaints Queue',
    sub: 'Verified and resolved exclusively by Food Staff. Verify & forward to Admin for token approval, then resolve on-site.',
    color: '#d97706'
  } : isWarden ? {
    title: 'Hostel Warden Complaints Queue',
    sub: 'Handled by Hostel Warden. Verify issues & forward to Admin for token approval, then resolve on-site.',
    color: '#7c3aed'
  } : {
    title: 'Hostel Complaints Master Administration Queue',
    sub: 'Review forwarded complaints from Wardens & Food Staff, approve & award Green Tokens, and confirm final closure.',
    color: '#059669'
  };

  return (
    <div>
      {/* Toast notification overlay */}
      <ToastNotification toast={toast} onDismiss={() => setToast(null)} />

      {/* Header & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28, flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10, letterSpacing: '-0.5px' }}>
            <ShieldCheck color={headerInfo.color} size={26} /> {headerInfo.title}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>
            {headerInfo.sub}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <Filter size={16} color="var(--text-subtle)" />
          {/* Status filter */}
          <select
            id="staff-queue-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="form-select"
            style={{ width: 'auto', padding: '9px 16px' }}
          >
            <option value="">All Statuses</option>
            <option value="Submitted">Submitted</option>
            <option value="Verified by Food Staff">Verified by Food Staff</option>
            <option value="Verified by Warden">Verified by Warden</option>
            <option value="Admin Verified">Admin Verified</option>
            <option value="Work Completed">Work Completed</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
          {/* Hostel type filter */}
          <select
            id="staff-hostel-filter"
            value={hostelFilter}
            onChange={(e) => setHostelFilter(e.target.value)}
            className="form-select"
            style={{ width: 'auto', padding: '9px 16px' }}
          >
            <option value="">All Hostels</option>
            <option value="Boys Hostel">Boys Hostel</option>
            <option value="Girls Hostel">Girls Hostel</option>
            <option value="NRI Hostel">NRI Hostel</option>
          </select>
          {/* Category filter */}
          <select
            id="staff-category-filter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="form-select"
            style={{ width: 'auto', padding: '9px 16px' }}
          >
            <option value="">All Categories</option>
            {['Electrical','Plumbing','Cleanliness','Food/Mess','Internet/Network','Furniture','Pest Control','Water Supply','Other'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button id="staff-queue-refresh" onClick={loadReports} className="btn btn-outline" style={{ padding: '9px 16px' }}>
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner-error" style={{ marginBottom: 20 }}>
          <AlertCircle size={18} color="#dc2626" style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Reports List */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)', padding: 60, textAlign: 'center', fontSize: 14, fontWeight: 500 }}>
          Loading hostel complaints...
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card" style={{ color: 'var(--text-subtle)', padding: 60, textAlign: 'center' }}>
          No complaints found matching the selected filters.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {reports.map((r) => {
            const st = statusStyles(r.status);
            const isFood = r.food_related || r.category === 'Food/Mess' || r.category === 'Food & Mess';
            const isSubmitted = r.status === 'Submitted' || r.status === 'Under Review';
            const isForwardedToAdmin = ['Verified by Food Staff', 'Verified by Warden'].includes(r.status);
            const isAdminVerified = r.status === 'Admin Verified' || r.status === 'In Progress' || r.status === 'Verified';
            const isWorkCompleted = r.status === 'Work Completed';
            const isResolved = r.status === 'Resolved';
            const isRejected = r.status === 'Rejected';

            return (
              <div
                key={r.id}
                className="glass-card"
                style={{
                  padding: 22,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  borderLeft: isResolved ? '4px solid #059669' :
                              isAdminVerified ? '4px solid #10b981' :
                              isForwardedToAdmin ? '4px solid #7c3aed' :
                              '4px solid #3b82f6'
                }}
              >
                {/* Main Card Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    {r.photo_path ? (
                      <img
                        src={`http://localhost:8000/${r.photo_path}`}
                        alt="Issue"
                        onError={(e) => { e.target.style.display = 'none'; }}
                        style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc' }}
                      />
                    ) : (
                      <div style={{ width: 56, height: 56, borderRadius: 12, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #a7f3d0' }}>
                        <Clock size={22} color="#059669" />
                      </div>
                    )}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                        <span style={{ color: 'var(--text-main)', fontSize: 16, fontWeight: 800 }}>Complaint #{r.id}</span>
                        <span style={{ padding: '4px 12px', borderRadius: 999, fontSize: 11, fontWeight: 700, background: st.bg, color: st.text, border: `1px solid ${st.border}` }}>
                          {r.status}
                        </span>
                        {r.category && (
                          <span style={{ padding: '3px 10px', borderRadius: 8, fontSize: 11, fontWeight: 700, background: isFood ? '#fef3c7' : '#f1f5f9', color: isFood ? '#92400e' : '#475569', border: isFood ? '1px solid #fde68a' : '1px solid #cbd5e1' }}>
                            {isFood && '🍽 '}{r.category}
                          </span>
                        )}
                        {isAdminVerified && (
                          <span className="badge badge-emerald" style={{ fontSize: 11 }}>
                            <Coins size={13} /> 10 Tokens Generated
                          </span>
                        )}
                      </div>
                      <div style={{ color: 'var(--text-main)', fontSize: 14, marginTop: 4, fontWeight: 700 }}>
                        {r.hostel_type && <span style={{ color: '#7c3aed', marginRight: 6 }}>{r.hostel_type} ›</span>}
                        {r.location} {r.building && `(${r.building})`} {r.floor && `· ${r.floor}`}
                      </div>
                      <div style={{ color: 'var(--text-subtle)', fontSize: 12, marginTop: 2, fontWeight: 500 }}>
                        Submitted on {new Date(r.created_at).toLocaleString()} {r.reporter_name && `by ${r.reporter_name}`}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => openHistory(r)}
                    className="btn btn-outline"
                    style={{ fontSize: 12, padding: '7px 14px', borderRadius: 8 }}
                  >
                    <History size={14} /> Audit History
                  </button>
                </div>

                {r.description && (
                  <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: 0, padding: '10px 14px', background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', lineHeight: 1.5 }}>
                    {r.description}
                  </p>
                )}

                {/* Lifecycle Action Bar */}
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 14 }}>
                  {/* Status progression banner */}
                  <div style={{ marginBottom: 12 }}>
                    {isSubmitted ? (
                      <span style={{ color: '#d97706', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Clock size={14} /> Step 1 of 5 – Submitted: Awaiting {isFood ? 'Food Staff' : 'Warden'} verification & forwarding to Admin
                      </span>
                    ) : isForwardedToAdmin ? (
                      <span style={{ color: '#7c3aed', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <ArrowRight size={14} /> Step 2 of 5 – Forwarded: Awaiting Admin verification & Green Token generation
                      </span>
                    ) : isAdminVerified ? (
                      <span style={{ color: '#059669', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Coins size={14} /> Step 3 of 5 – Admin Verified & Tokens Awarded: Awaiting {isFood ? 'Food Staff' : 'Warden'} to complete work on-site
                      </span>
                    ) : isWorkCompleted ? (
                      <span style={{ color: '#0369a1', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <CheckCircle size={14} /> Step 4 of 5 – Work Completed: Awaiting Admin final closure
                      </span>
                    ) : isResolved ? (
                      <span id={`report-${r.id}-resolved-label`} style={{ color: '#059669', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <CheckCircle size={14} /> Step 5 of 5 – Resolved & Closed by Admin ✓
                      </span>
                    ) : (
                      <span style={{ color: '#dc2626', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <AlertCircle size={14} /> Complaint Marked as Rejected
                      </span>
                    )}
                  </div>

                  {/* Optional reason note input */}
                  {activeReasonId === r.id && (
                    <div style={{ marginBottom: 12 }}>
                      <input
                        id={`reason-input-${r.id}`}
                        type="text"
                        placeholder="Optional note / remarks for this action..."
                        value={reasonInput}
                        onChange={(e) => setReasonInput(e.target.value)}
                        className="form-input"
                        style={{ fontSize: 13, padding: '9px 14px', borderRadius: 10 }}
                      />
                    </div>
                  )}

                  {/* Action Buttons based on User Role and Lifecycle State */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>

                    {/* ── STEP 2: Food Staff / Warden verifies & forwards to Admin ── */}
                    {/* Only shown to food_staff / warden when status is Submitted */}
                    {isSubmitted && (isFoodStaff || isWarden) && (
                      <button
                        id={`forward-btn-${r.id}`}
                        onClick={() => handleForwardToAdmin(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 18px', fontSize: 13, background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)' }}
                      >
                        <ShieldCheck size={15} /> {actionLoading === r.id ? 'Forwarding...' : 'Verify & Forward to Admin'}
                      </button>
                    )}

                    {/* Admin sees submitted complaints but cannot act until staff forwards */}
                    {isSubmitted && isAdmin && (
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, background: '#f5f3ff', color: '#7c3aed', fontSize: 12, fontWeight: 600, border: '1px solid #ddd6fe' }}>
                        <Clock size={14} color="#7c3aed" />
                        Awaiting {isFood ? 'Food Staff' : 'Warden'} verification & forwarding
                      </div>
                    )}

                    {/* ── STEP 3: Admin verifies after complaint has been forwarded ── */}
                    {/* Only shown to Admin when status is "Verified by Food Staff" or "Verified by Warden" */}
                    {isAdmin && isForwardedToAdmin && (
                      <button
                        id={`admin-verify-btn-${r.id}`}
                        onClick={() => handleAdminVerify(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 18px', fontSize: 13, background: 'linear-gradient(135deg, #059669 0%, #047857 100%)' }}
                      >
                        <Coins size={15} /> {actionLoading === r.id ? 'Verifying...' : 'Admin Verify & Award 10 Tokens'}
                      </button>
                    )}

                    {/* Food Staff / Warden see the complaint is pending Admin review after forwarding */}
                    {isForwardedToAdmin && (isFoodStaff || isWarden) && (
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, background: '#f5f3ff', color: '#7c3aed', fontSize: 12, fontWeight: 600, border: '1px solid #ddd6fe' }}>
                        <ArrowRight size={14} color="#7c3aed" />
                        Forwarded to Admin — awaiting Admin verification & token award
                      </div>
                    )}

                    {/* ── STEP 4: Food Staff / Warden marks work done after Admin Verified ── */}
                    {/* Only shown to food_staff / warden when status is "Admin Verified" */}
                    {isAdminVerified && (isFoodStaff || isWarden) && (
                      <button
                        id={`complete-btn-${r.id}`}
                        onClick={() => handleCompleteWork(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-secondary"
                        style={{ padding: '8px 18px', fontSize: 13, background: '#eff6ff', color: '#1d4ed8', borderColor: '#bfdbfe' }}
                      >
                        <CheckCircle size={15} /> {actionLoading === r.id ? 'Updating...' : 'Mark Work Completed & Report to Admin'}
                      </button>
                    )}

                    {/* Admin sees complaint is pending on-site work after Admin Verified */}
                    {isAdminVerified && isAdmin && (
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, background: '#fffbeb', color: '#b45309', fontSize: 12, fontWeight: 600, border: '1px solid #fde68a' }}>
                        <Clock size={14} color="#d97706" />
                        Tokens awarded — awaiting {isFood ? 'Food Staff' : 'Warden'} to complete work & report back
                      </div>
                    )}

                    {/* ── STEP 5: Admin closes complaint after Work Completed reported ── */}
                    {/* Only shown to Admin when status is "Work Completed" */}
                    {isAdmin && isWorkCompleted && (
                      <button
                        id={`admin-resolve-btn-${r.id}`}
                        onClick={() => handleAdminResolve(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 18px', fontSize: 13, background: 'linear-gradient(135deg, #059669 0%, #047857 100%)' }}
                      >
                        <CheckCircle size={15} /> {actionLoading === r.id ? 'Closing...' : 'Confirm & Close Complaint (Final Resolved)'}
                      </button>
                    )}

                    {/* Food Staff / Warden see Work Completed status is awaiting Admin closure */}
                    {isWorkCompleted && (isFoodStaff || isWarden) && (
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, background: '#e0f2fe', color: '#0369a1', fontSize: 12, fontWeight: 600, border: '1px solid #bae6fd' }}>
                        <CheckCircle size={14} color="#0369a1" />
                        Work reported complete — awaiting Admin final closure
                      </div>
                    )}

                    {/* Reject button */}
                    {!isResolved && !isRejected && (
                      <button
                        id={`reject-btn-${r.id}`}
                        onClick={() => handleReject(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-danger"
                        style={{ padding: '8px 14px', fontSize: 12 }}
                      >
                        Reject
                      </button>
                    )}

                    {/* Add note toggle */}
                    {!isResolved && !isRejected && (
                      <button
                        id={`note-btn-${r.id}`}
                        onClick={() => setActiveReasonId(activeReasonId === r.id ? null : r.id)}
                        className="btn btn-outline"
                        style={{ padding: '8px 12px', fontSize: 12 }}
                      >
                        {activeReasonId === r.id ? 'Hide Note' : '+ Add Note'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Audit Trail Modal */}
      {selectedReport && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 }}>
          <div className="glass-card" style={{ maxWidth: 540, width: '100%', maxHeight: '85vh', overflowY: 'auto', padding: 28 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, borderBottom: '1px solid #e2e8f0', paddingBottom: 14 }}>
              <div>
                <h3 style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 800, margin: 0 }}>Complaint #{selectedReport.id} – Status History</h3>
                <span style={{ color: 'var(--text-subtle)', fontSize: 12, fontWeight: 500 }}>
                  {selectedReport.hostel_type && `${selectedReport.hostel_type} › `}{selectedReport.location}
                  {selectedReport.category && ` · ${selectedReport.category}`}
                </span>
              </div>
              <button onClick={() => setSelectedReport(null)} style={{ background: '#f1f5f9', border: 'none', color: '#64748b', cursor: 'pointer', padding: 8, borderRadius: 10 }}>
                <X size={18} />
              </button>
            </div>

            {historyLoading ? (
              <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-subtle)' }}>Loading timeline...</div>
            ) : history.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-subtle)' }}>No history entries recorded yet.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {history.map((h, i) => (
                  <div key={h.id || i} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#059669', marginTop: 5, flexShrink: 0 }} />
                    <div style={{ flex: 1, background: '#f8fafc', padding: '12px 16px', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-main)' }}>
                          {h.from_status ? `${h.from_status} → ${h.to_status}` : h.to_status}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--text-subtle)' }}>{new Date(h.changed_at).toLocaleString()}</span>
                      </div>
                      {h.reason && (
                        <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>{h.reason}</p>
                      )}
                      {h.changed_by_name && (
                        <span style={{ fontSize: 11, color: '#7c3aed', display: 'block', marginTop: 4 }}>By: {h.changed_by_name}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

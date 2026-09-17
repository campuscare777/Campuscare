import { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle, ShieldCheck, History, ChevronRight, Filter, Eye, RefreshCw, X, Coins } from 'lucide-react';
import { reportsAPI } from './api';

export default function StaffReportsQueue({ onReportUpdated }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [reasonInput, setReasonInput] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const loadReports = () => {
    setLoading(true);
    reportsAPI
      .list(filter || undefined)
      .then((res) => {
        setReports(res.data.reports || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load staff reports queue:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadReports();
  }, [filter]);

  const handleVerify = async (reportId) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      let res;
      try {
        res = await reportsAPI.verify(reportId, reasonInput || 'Report verified by maintenance staff');
      } catch (e1) {
        res = await reportsAPI.updateStatus(reportId, 'Verified', reasonInput || 'Report verified by maintenance staff');
      }
      setReasonInput('');
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to verify report');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStatusChange = async (reportId, newStatus) => {
    setActionLoading(reportId);
    setErrorMessage('');
    try {
      const res = await reportsAPI.updateStatus(reportId, newStatus, reasonInput || undefined);
      setReasonInput('');
      loadReports();
      if (selectedReport && selectedReport.id === reportId) {
        setSelectedReport(res.data);
      }
      if (onReportUpdated) onReportUpdated();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : `Failed to update status to ${newStatus}`);
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
    Reported: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
    Submitted: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
    Verified: { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe' },
    'In Progress': { bg: '#fffbeb', text: '#d97706', border: '#fde68a' },
    Resolved: { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' },
    Rejected: { bg: '#fef2f2', text: '#dc2626', border: '#fecaca' },
  }[s] || { bg: '#f8fafc', text: '#64748b', border: '#e2e8f0' });

  return (
    <div>
      {/* Header & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28, flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10, letterSpacing: '-0.5px' }}>
            <ShieldCheck color="#7c3aed" size={26} /> Staff Maintenance Queue & Verification
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>
            Verify issues & manage report status lifecycle: Reported → Verified → In Progress → Resolved
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Filter size={16} color="var(--text-subtle)" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="form-select"
            style={{ width: 'auto', padding: '9px 16px' }}
          >
            <option value="">All Statuses</option>
            <option value="Reported">Reported (Unverified)</option>
            <option value="Verified">Verified</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
          <button onClick={loadReports} className="btn btn-outline" style={{ padding: '9px 16px' }}>
            <RefreshCw size={15} /> Refresh Queue
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner-error">
          <AlertCircle size={18} color="#dc2626" style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Reports List */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)', padding: 60, textAlign: 'center', fontSize: 14, fontWeight: 500 }}>
          Loading maintenance queue...
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card" style={{ color: 'var(--text-subtle)', padding: 60, textAlign: 'center' }}>
          No maintenance reports found matching filter.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {reports.map((r) => {
            const isVerified = r.verified || r.verified_at || ['Verified', 'In Progress', 'Resolved'].includes(r.status);
            const isUnverified = r.status === 'Reported' || r.status === 'Submitted';
            const st = statusStyles(r.status);

            return (
              <div
                key={r.id}
                className="glass-card"
                style={{
                  padding: 22,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  borderLeft: isVerified ? '4px solid #059669' : '4px solid #3b82f6'
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
                        <span style={{ color: 'var(--text-main)', fontSize: 16, fontWeight: 800 }}>Report #{r.id}</span>
                        <span style={{ padding: '4px 12px', borderRadius: 999, fontSize: 11, fontWeight: 700, background: st.bg, color: st.text, border: `1px solid ${st.border}` }}>
                          {r.status}
                        </span>
                        {isVerified && (
                          <span className="badge badge-purple" style={{ fontSize: 11 }}>
                            <ShieldCheck size={13} /> Verified
                          </span>
                        )}
                        {r.eligible_for_token && (
                          <span className="badge badge-amber" style={{ fontSize: 11 }}>
                            <Coins size={13} /> Token Eligible
                          </span>
                        )}
                      </div>
                      <div style={{ color: 'var(--text-main)', fontSize: 14, marginTop: 4, fontWeight: 700 }}>
                        {r.location} {r.building && `(${r.building})`}
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
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: 14, flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    {isUnverified ? (
                      <span style={{ color: '#d97706', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        ⚠️ Pending Staff Verification
                      </span>
                    ) : (
                      <span style={{ color: '#059669', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                        ✓ Verified & Active in Maintenance Workflow
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {/* Action 1: Verify Report */}
                    {isUnverified && (
                      <button
                        onClick={() => handleVerify(r.id)}
                        disabled={actionLoading === r.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 18px', fontSize: 13, background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)' }}
                      >
                        <ShieldCheck size={15} /> {actionLoading === r.id ? 'Verifying...' : 'Verify Report'}
                      </button>
                    )}

                    {/* Action 2: Start Progress */}
                    {r.status === 'Verified' && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'In Progress')}
                        disabled={actionLoading === r.id}
                        className="btn btn-secondary"
                        style={{ padding: '8px 18px', fontSize: 13, background: '#fffbeb', color: '#d97706', borderColor: '#fde68a' }}
                      >
                        {actionLoading === r.id ? 'Updating...' : 'Start Progress'}
                      </button>
                    )}

                    {/* Action 3: Mark Resolved */}
                    {(r.status === 'Verified' || r.status === 'In Progress') && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'Resolved')}
                        disabled={actionLoading === r.id}
                        className="btn btn-primary"
                        style={{ padding: '8px 18px', fontSize: 13 }}
                      >
                        <CheckCircle size={15} /> {actionLoading === r.id ? 'Resolving...' : 'Mark Resolved'}
                      </button>
                    )}

                    {/* Reject Option */}
                    {r.status !== 'Resolved' && r.status !== 'Rejected' && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'Rejected')}
                        disabled={actionLoading === r.id}
                        className="btn btn-danger"
                        style={{ padding: '8px 14px', fontSize: 12 }}
                      >
                        Reject
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
                <h3 style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 800, margin: 0 }}>Report #{selectedReport.id} Status History</h3>
                <span style={{ color: 'var(--text-subtle)', fontSize: 12, fontWeight: 500 }}>Location: {selectedReport.location}</span>
              </div>
              <button onClick={() => setSelectedReport(null)} style={{ background: '#f1f5f9', border: 'none', color: '#64748b', cursor: 'pointer', padding: 8, borderRadius: 10 }}>
                <X size={18} />
              </button>
            </div>

            {historyLoading ? (
              <div style={{ color: 'var(--text-muted)', padding: 30, textAlign: 'center' }}>Loading audit history...</div>
            ) : history.length === 0 ? (
              <div style={{ color: 'var(--text-subtle)', padding: 30, textAlign: 'center' }}>No status transitions recorded yet.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {history.map((h, i) => (
                  <div key={i} style={{ padding: 14, background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className="badge badge-blue">{h.from_status}</span>
                        <ChevronRight size={14} color="var(--text-subtle)" />
                        <span className="badge badge-emerald">{h.to_status}</span>
                      </div>
                      <span style={{ color: 'var(--text-subtle)', fontSize: 11, fontWeight: 500 }}>{new Date(h.changed_at).toLocaleString()}</span>
                    </div>
                    {h.reason && <p style={{ color: 'var(--text-main)', fontSize: 13, margin: '6px 0 0', fontWeight: 500, fontStyle: 'italic' }}>"{h.reason}"</p>}
                    {h.changed_by_name && <span style={{ color: 'var(--text-subtle)', fontSize: 11, display: 'block', marginTop: 4 }}>Changed by: {h.changed_by_name}</span>}
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

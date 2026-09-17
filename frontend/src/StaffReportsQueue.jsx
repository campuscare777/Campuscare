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
      const res = await reportsAPI.verify(reportId, reasonInput || 'Report verified by maintenance staff');
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

  const statusColor = (s) => ({
    Reported: '#3b82f6',
    Submitted: '#3b82f6',
    Verified: '#a855f7',
    'In Progress': '#eab308',
    Resolved: '#22c55e',
    Rejected: '#ef4444',
  }[s] || '#64748b');

  return (
    <div>
      {/* Header & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ color: 'white', fontSize: 20, fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldCheck color="#a855f7" size={22} /> Staff Maintenance Queue & Verification
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 12, margin: '4px 0 0' }}>SCRUM05-F002 Status Progression Lifecycle: Reported → Verified → In Progress → Resolved</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Filter size={15} color="#64748b" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ padding: '8px 14px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, outline: 'none' }}
          >
            <option value="">All Statuses</option>
            <option value="Reported">Reported (Unverified)</option>
            <option value="Verified">Verified</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
          <button onClick={loadReports} style={{ padding: '8px 12px', background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {errorMessage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, marginBottom: 18 }}>
          <AlertCircle size={18} color="#ef4444" style={{ flexShrink: 0 }} />
          <span style={{ color: '#fca5a5', fontSize: 13 }}>{errorMessage}</span>
        </div>
      )}

      {/* Reports Table Queue */}
      {loading ? (
        <div style={{ color: '#94a3b8', padding: 40, textAlign: 'center', background: '#1e293b', borderRadius: 12, border: '1px solid #334155' }}>
          Loading maintenance queue...
        </div>
      ) : reports.length === 0 ? (
        <div style={{ color: '#64748b', padding: 40, textAlign: 'center', background: '#1e293b', borderRadius: 12, border: '1px solid #334155' }}>
          No maintenance reports found in queue.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {reports.map((r) => {
            const isVerified = r.verified || r.verified_at || ['Verified', 'In Progress', 'Resolved'].includes(r.status);
            const isUnverified = r.status === 'Reported' || r.status === 'Submitted';

            return (
              <div
                key={r.id}
                style={{
                  background: '#1e293b',
                  borderRadius: 12,
                  padding: 18,
                  border: `1px solid ${isVerified ? '#3b82f640' : '#334155'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 14,
                  transition: 'all 0.2s',
                }}
              >
                {/* Main Card Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    {r.photo_path ? (
                      <img
                        src={`http://localhost:8000/${r.photo_path}`}
                        alt="Issue"
                        onError={(e) => { e.target.style.display = 'none'; }}
                        style={{ width: 52, height: 52, objectFit: 'cover', borderRadius: 8, border: '1px solid #334155', background: '#0f172a' }}
                      />
                    ) : (
                      <div style={{ width: 52, height: 52, borderRadius: 8, background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #334155' }}>
                        <Clock size={20} color="#64748b" />
                      </div>
                    )}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ color: 'white', fontSize: 15, fontWeight: 700 }}>Report #{r.id}</span>
                        <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: `${statusColor(r.status)}20`, color: statusColor(r.status) }}>
                          {r.status}
                        </span>
                        {isVerified && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600, background: 'rgba(168,85,247,0.15)', color: '#a855f7' }}>
                            <ShieldCheck size={12} /> Verified
                          </span>
                        )}
                        {r.eligible_for_token && (
                          <span style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600, background: 'rgba(234,179,8,0.15)', color: '#eab308' }}>
                            <Coins size={12} /> Token Eligible
                          </span>
                        )}
                      </div>
                      <div style={{ color: '#cbd5e1', fontSize: 13, marginTop: 4, fontWeight: 500 }}>{r.location} {r.building && `(${r.building})`}</div>
                      <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>
                        Submitted on {new Date(r.created_at).toLocaleString()} {r.reporter_name && `by ${r.reporter_name}`}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => openHistory(r)}
                    style={{ padding: '6px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: '#94a3b8', fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <History size={14} /> Audit Trail
                  </button>
                </div>

                {r.description && (
                  <p style={{ color: '#94a3b8', fontSize: 12, margin: 0, padding: '8px 12px', background: '#0f172a', borderRadius: 6, border: '1px solid #1e293b' }}>
                    {r.description}
                  </p>
                )}

                {/* Lifecycle Action Buttons Bar */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #334155', paddingTop: 12, flexWrap: 'wrap', gap: 10 }}>
                  <div style={{ color: '#64748b', fontSize: 12 }}>
                    {isUnverified ? (
                      <span style={{ color: '#f59e0b', fontSize: 12, fontWeight: 500 }}>⚠️ Unverified: Must be verified before progressing to In Progress / Resolved</span>
                    ) : (
                      <span style={{ color: '#22c55e', fontSize: 12, fontWeight: 500 }}>✓ Verified report — Eligible for lifecycle progression</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {/* Action 1: Verify Report */}
                    {isUnverified && (
                      <button
                        onClick={() => handleVerify(r.id)}
                        disabled={actionLoading === r.id}
                        style={{
                          padding: '8px 16px',
                          background: 'linear-gradient(135deg, #a855f7, #9333ea)',
                          color: 'white',
                          border: 'none',
                          borderRadius: 8,
                          fontSize: 12,
                          fontWeight: 600,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}
                      >
                        <ShieldCheck size={14} /> {actionLoading === r.id ? 'Verifying...' : 'Verify Report'}
                      </button>
                    )}

                    {/* Action 2: Start Progress (Only if Verified) */}
                    {r.status === 'Verified' && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'In Progress')}
                        disabled={actionLoading === r.id}
                        style={{
                          padding: '8px 16px',
                          background: '#eab308',
                          color: '#0f172a',
                          border: 'none',
                          borderRadius: 8,
                          fontSize: 12,
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {actionLoading === r.id ? 'Updating...' : 'Start Progress'}
                      </button>
                    )}

                    {/* Action 3: Mark Resolved (Requires prior verification) */}
                    {(r.status === 'Verified' || r.status === 'In Progress') && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'Resolved')}
                        disabled={actionLoading === r.id}
                        style={{
                          padding: '8px 16px',
                          background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                          color: 'white',
                          border: 'none',
                          borderRadius: 8,
                          fontSize: 12,
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {actionLoading === r.id ? 'Resolving...' : 'Mark Resolved'}
                      </button>
                    )}

                    {/* Reject Option */}
                    {r.status !== 'Resolved' && r.status !== 'Rejected' && (
                      <button
                        onClick={() => handleStatusChange(r.id, 'Rejected')}
                        disabled={actionLoading === r.id}
                        style={{
                          padding: '8px 14px',
                          background: 'rgba(239,68,68,0.1)',
                          border: '1px solid rgba(239,68,68,0.3)',
                          color: '#ef4444',
                          borderRadius: 8,
                          fontSize: 12,
                          fontWeight: 500,
                          cursor: 'pointer',
                        }}
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
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 }}>
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, border: '1px solid #334155', maxWidth: 540, width: '100%', maxHeight: '85vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18, borderBottom: '1px solid #334155', paddingBottom: 12 }}>
              <div>
                <h3 style={{ color: 'white', fontSize: 16, fontWeight: 700, margin: 0 }}>Report #{selectedReport.id} Status Audit History</h3>
                <span style={{ color: '#94a3b8', fontSize: 12 }}>Location: {selectedReport.location}</span>
              </div>
              <button onClick={() => setSelectedReport(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {historyLoading ? (
              <div style={{ color: '#94a3b8', padding: 20, textAlign: 'center' }}>Loading audit history...</div>
            ) : history.length === 0 ? (
              <div style={{ color: '#64748b', padding: 20, textAlign: 'center' }}>No status transitions recorded yet.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {history.map((h, i) => (
                  <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8, border: '1px solid #334155', fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ color: statusColor(h.from_status), fontWeight: 600 }}>{h.from_status}</span>
                        <ChevronRight size={14} color="#64748b" />
                        <span style={{ color: statusColor(h.to_status), fontWeight: 600 }}>{h.to_status}</span>
                      </div>
                      <span style={{ color: '#64748b', fontSize: 11 }}>{new Date(h.changed_at).toLocaleString()}</span>
                    </div>
                    {h.reason && <p style={{ color: '#cbd5e1', fontSize: 12, margin: 0 }}>Reason: {h.reason}</p>}
                    {h.changed_by_name && <span style={{ color: '#64748b', fontSize: 10, display: 'block', marginTop: 4 }}>Changed by: {h.changed_by_name}</span>}
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

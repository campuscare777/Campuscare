import React, { useState, useEffect } from 'react';
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  ChevronRight,
  Filter,
  RefreshCw,
  Search,
  Upload,
  ArrowLeft,
  ArrowRight,
  X,
  History,
  Coins,
  MapPin,
  Building,
  Image as ImageIcon,
} from 'lucide-react';
import { reportsAPI } from './api';

export default function StudentReportsView({ onOpenReportForm }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadReports = () => {
    setLoading(true);
    reportsAPI
      .list(filter || undefined)
      .then((res) => {
        setReports(res.data.reports || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load student reports:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadReports();
  }, [filter]);

  const openDetail = async (report) => {
    setSelectedReport(report);
    setHistoryLoading(true);
    try {
      const res = await reportsAPI.getHistory(report.id);
      setHistory(res.data || []);
    } catch (err) {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const statusConfig = (status) => {
    switch (status) {
      case 'Submitted':
      case 'Reported':
        return {
          bg: '#eff6ff',
          text: '#2563eb',
          border: '#bfdbfe',
          icon: Clock,
          label: 'Submitted (Pending Review)',
          desc: 'Your complaint has been received and is waiting for staff/warden verification.',
        };
      case 'Verified by Food Staff':
      case 'Verified by Warden':
        return {
          bg: '#f5f3ff',
          text: '#7c3aed',
          border: '#ddd6fe',
          icon: ArrowRight,
          label: status,
          desc: 'Verified by staff and forwarded to Admin for token approval!',
        };
      case 'Admin Verified':
      case 'Verified':
        return {
          bg: '#ecfdf5',
          text: '#059669',
          border: '#a7f3d0',
          icon: ShieldCheck,
          label: 'Admin Verified (Tokens Awarded!)',
          desc: 'Admin approved this complaint! 10 Green Tokens have been awarded to your account.',
        };
      case 'In Progress':
        return {
          bg: '#fffbeb',
          text: '#d97706',
          border: '#fde68a',
          icon: AlertCircle,
          label: 'In Progress',
          desc: 'Hostel crew is actively resolving this complaint on-site.',
        };
      case 'Work Completed':
        return {
          bg: '#e0f2fe',
          text: '#0369a1',
          border: '#bae6fd',
          icon: CheckCircle,
          label: 'Work Completed (Pending Admin Closure)',
          desc: 'Staff completed resolution on-site and reported to Admin for final closure.',
        };
      case 'Resolved':
        return {
          bg: '#ecfdf5',
          text: '#059669',
          border: '#a7f3d0',
          icon: CheckCircle,
          label: 'Resolved & Closed',
          desc: 'Complaint confirmed resolved and closed by Admin.',
        };
      case 'Rejected':
        return {
          bg: '#fef2f2',
          text: '#dc2626',
          border: '#fecaca',
          icon: X,
          label: 'Rejected',
          desc: 'This complaint could not be verified or was marked invalid.',
        };
      default:
        return {
          bg: '#f8fafc',
          text: '#64748b',
          border: '#e2e8f0',
          icon: Clock,
          label: status,
          desc: 'Report registered in system.',
        };
    }
  };

  // Filter & search filtering
  const filteredReports = reports.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (r.location && r.location.toLowerCase().includes(q)) ||
      (r.building && r.building.toLowerCase().includes(q)) ||
      (r.area && r.area.toLowerCase().includes(q)) ||
      (r.description && r.description.toLowerCase().includes(q)) ||
      String(r.id).includes(q)
    );
  });

  // Metrics
  const totalCount = reports.length;
  const pendingCount = reports.filter((r) => r.status === 'Submitted' || r.status === 'Reported').length;
  const inProgressCount = reports.filter((r) => r.status === 'Verified' || r.status === 'In Progress').length;
  const resolvedCount = reports.filter((r) => r.status === 'Resolved').length;

  const getPhotoUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    const clean = path.replace(/^[/\\]+/, '');
    return `http://localhost:8000/${clean}`;
  };

  return (
    <div id="student-reports-screen" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 28,
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #059669, #10b981)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(5, 150, 105, 0.25)',
              }}
            >
              <FileText size={20} color="#fff" />
            </div>
            <h2
              id="student-reports-title"
              style={{
                color: 'var(--text-main)',
                fontSize: 26,
                fontWeight: 800,
                margin: 0,
                letterSpacing: '-0.5px',
              }}
            >
              My Hostel Complaints
            </h2>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>
            Track the status of your reported hostel complaints, cleanliness, and maintenance issues
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {onOpenReportForm && (
            <button
              id="btn-report-new-issue"
              onClick={onOpenReportForm}
              className="btn btn-primary"
              style={{ padding: '11px 22px', fontSize: 14 }}
            >
              <Upload size={16} /> Report Hostel Complaint
            </button>
          )}
        </div>
      </div>

      {/* Quick Status Metric Pills */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginBottom: 28,
        }}
      >
        <div
          className="glass-card"
          style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16 }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <FileText size={22} color="#475569" />
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
              Total Reports
            </div>
            <div id="metric-total-reports" style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-main)', marginTop: 2 }}>
              {totalCount}
            </div>
          </div>
        </div>

        <div
          className="glass-card"
          style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16 }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: '#eff6ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Clock size={22} color="#2563eb" />
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#2563eb', textTransform: 'uppercase' }}>
              Submitted
            </div>
            <div id="metric-pending-reports" style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-main)', marginTop: 2 }}>
              {pendingCount}
            </div>
          </div>
        </div>

        <div
          className="glass-card"
          style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16 }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: '#f5f3ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldCheck size={22} color="#7c3aed" />
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#7c3aed', textTransform: 'uppercase' }}>
              In Progress
            </div>
            <div id="metric-inprogress-reports" style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-main)', marginTop: 2 }}>
              {inProgressCount}
            </div>
          </div>
        </div>

        <div
          className="glass-card"
          style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16 }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: '#ecfdf5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircle size={22} color="#059669" />
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>
              Resolved
            </div>
            <div id="metric-resolved-reports" style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-main)', marginTop: 2 }}>
              {resolvedCount}
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="glass-card"
        style={{
          padding: '16px 20px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 14,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 260 }}>
          <Search size={18} color="var(--text-subtle)" />
          <input
            id="student-search-input"
            type="text"
            placeholder="Search by hostel, block, floor, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input"
            style={{ border: 'none', background: 'transparent', padding: '6px 0', fontSize: 14, width: '100%' }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-subtle)' }}
            >
              <X size={16} />
            </button>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Filter size={16} color="var(--text-subtle)" />
          <select
            id="student-status-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="form-select"
            style={{ width: 'auto', padding: '8px 16px', fontSize: 13 }}
          >
            <option value="">All Statuses</option>
            <option value="Submitted">Submitted</option>
            <option value="Verified by Food Staff">Verified by Food Staff</option>
            <option value="Verified by Warden">Verified by Warden</option>
            <option value="Admin Verified">Admin Verified</option>
            <option value="In Progress">In Progress</option>
            <option value="Work Completed">Work Completed</option>
            <option value="Resolved">Resolved</option>
            <option value="Rejected">Rejected</option>
          </select>
          <button
            id="student-refresh-btn"
            onClick={loadReports}
            className="btn btn-outline"
            style={{ padding: '8px 14px', fontSize: 13 }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="glass-card" style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="spin" style={{ marginBottom: 12 }} />
          <div>Loading your hostel complaints...</div>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: 60, color: 'var(--text-subtle)' }}>
          <FileText size={48} color="#cbd5e1" style={{ marginBottom: 14 }} />
          <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            {reports.length === 0 ? 'No complaints submitted yet' : 'No complaints match the selected filter'}
          </p>
          <p style={{ fontSize: 13, marginTop: 8, color: 'var(--text-muted)' }}>
            {reports.length === 0
              ? 'Click "Report Hostel Complaint" above to submit your first complaint.'
              : 'Try clearing the search or status filter to view all your complaints.'}
          </p>
        </div>
      ) : (
        <div id="student-reports-list" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filteredReports.map((r) => {
            const cfg = statusConfig(r.status);
            const StatusIcon = cfg.icon;
            return (
              <div
                key={r.id}
                id={`student-report-card-${r.id}`}
                onClick={() => openDetail(r)}
                className="glass-card glass-card-interactive"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '18px 24px',
                  cursor: 'pointer',
                  borderLeft: `4px solid ${cfg.text}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 14,
                      background: cfg.bg,
                      border: `1px solid ${cfg.border}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <StatusIcon size={22} color={cfg.text} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ color: 'var(--text-main)', fontSize: 16, fontWeight: 800 }}>
                        Complaint #{r.id} &mdash; {r.hostel_type || r.location}
                      </span>
                      {r.category && (
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 700,
                          background: (r.food_related || r.category === 'Food & Mess' || r.category === 'Food/Mess') ? '#fef3c7' : '#f1f5f9',
                          color: (r.food_related || r.category === 'Food & Mess' || r.category === 'Food/Mess') ? '#92400e' : '#475569',
                          border: (r.food_related || r.category === 'Food & Mess' || r.category === 'Food/Mess') ? '1px solid #fde68a' : '1px solid #e2e8f0',
                        }}>
                          {(r.food_related || r.category === 'Food & Mess' || r.category === 'Food/Mess') ? '🍽 ' : ''}{r.category}
                        </span>
                      )}
                    </div>
                    <div style={{ color: 'var(--text-subtle)', fontSize: 13, marginTop: 4, fontWeight: 500 }}>
                      {r.building && `${r.building}`}
                      {r.floor && `, ${r.floor}`}
                      {r.area && ` — ${r.area}`}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
                  <span
                    id={`report-status-${r.id}`}
                    style={{
                      padding: '5px 14px',
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 700,
                      background: cfg.bg,
                      color: cfg.text,
                      border: `1px solid ${cfg.border}`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <StatusIcon size={13} />
                    {r.status}
                  </span>
                  <span style={{ color: 'var(--text-subtle)', fontSize: 12, fontWeight: 500 }}>
                    {new Date(r.created_at).toLocaleDateString()}
                  </span>
                  <ChevronRight size={18} color="var(--text-subtle)" />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Report Detail Modal */}
      {selectedReport && (
        <div
          id="report-detail-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.55)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
            padding: 20,
          }}
          onClick={() => setSelectedReport(null)}
        >
          <div
            id="report-detail-modal"
            className="glass-card"
            style={{
              width: '100%',
              maxWidth: 680,
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 30,
              background: '#ffffff',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 20,
                borderBottom: '1px solid #f1f5f9',
                paddingBottom: 16,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <h3
                  id="detail-modal-title"
                  style={{ color: 'var(--text-main)', fontSize: 20, fontWeight: 800, margin: 0 }}
                >
                  Complaint #{selectedReport.id} Details
                </h3>
                {(() => {
                  const cfg = statusConfig(selectedReport.status);
                  const Icon = cfg.icon;
                  return (
                    <span
                      id="detail-status-badge"
                      style={{
                        padding: '4px 12px',
                        borderRadius: 999,
                        fontSize: 12,
                        fontWeight: 700,
                        background: cfg.bg,
                        color: cfg.text,
                        border: `1px solid ${cfg.border}`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <Icon size={13} />
                      {selectedReport.status}
                    </span>
                  );
                })()}
              </div>
              <button
                id="btn-close-detail"
                onClick={() => setSelectedReport(null)}
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: 10,
                  padding: 6,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <X size={18} color="var(--text-main)" />
              </button>
            </div>

            {/* Real-time Status Card */}
            {(() => {
              const cfg = statusConfig(selectedReport.status);
              const Icon = cfg.icon;
              return (
                <div
                  id="detail-status-banner"
                  style={{
                    padding: '16px 20px',
                    borderRadius: 14,
                    background: cfg.bg,
                    border: `1px solid ${cfg.border}`,
                    marginBottom: 22,
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 14,
                  }}
                >
                  <div style={{ marginTop: 2 }}>
                    <Icon size={22} color={cfg.text} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 800, fontSize: 14, color: cfg.text, marginBottom: 3 }}>
                      Current Status: {selectedReport.status}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-main)', lineHeight: 1.5 }}>
                      {cfg.desc}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Photo Preview if present */}
            {selectedReport.photo_path && (
              <div style={{ marginBottom: 22 }}>
                <label
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--text-subtle)',
                    display: 'block',
                    marginBottom: 8,
                    letterSpacing: '0.5px',
                  }}
                >
                  Attached Photo Evidence
                </label>
                <div
                  style={{
                    borderRadius: 14,
                    overflow: 'hidden',
                    border: '1px solid #e2e8f0',
                    background: '#f8fafc',
                    maxHeight: 260,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <img
                    id="detail-photo-preview"
                    src={getPhotoUrl(selectedReport.photo_path)}
                    alt="Report Evidence"
                    style={{ width: '100%', maxHeight: 260, objectFit: 'contain' }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              </div>
            )}

            {/* Location Details Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                marginBottom: 20,
              }}
            >
              {[
                ['Hostel Type', selectedReport.hostel_type || selectedReport.location],
                ['Category', selectedReport.category || 'General'],
                ['Block / Wing', selectedReport.building || '—'],
                ['Floor', selectedReport.floor || '—'],
                ['Room / Area', selectedReport.area || '—'],
                ['Food / Mess Issue', (selectedReport.food_related || selectedReport.category === 'Food & Mess' || selectedReport.category === 'Food/Mess') ? 'Yes' : 'No'],
                ['Assigned Team', selectedReport.assigned_team || 'Not Assigned'],
                ['Resolved At', selectedReport.resolved_at ? new Date(selectedReport.resolved_at).toLocaleString() : '—'],
              ].map(([label, val]) => (
                <div
                  key={label}
                  style={{
                    padding: '12px 16px',
                    background: '#f8fafc',
                    borderRadius: 12,
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <span
                    style={{
                      color: 'var(--text-subtle)',
                      fontSize: 11,
                      display: 'block',
                      marginBottom: 4,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {label}
                  </span>
                  <span style={{ color: 'var(--text-main)', fontWeight: 700, fontSize: 13 }}>{val}</span>
                </div>
              ))}
            </div>

            {/* Description */}
            {selectedReport.description && (
              <div style={{ marginBottom: 22 }}>
                <label
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--text-subtle)',
                    display: 'block',
                    marginBottom: 6,
                    letterSpacing: '0.5px',
                  }}
                >
                  Description
                </label>
                <div
                  id="detail-description"
                  style={{
                    color: 'var(--text-main)',
                    fontSize: 13,
                    padding: '12px 16px',
                    background: '#f8fafc',
                    borderRadius: 12,
                    border: '1px solid #e2e8f0',
                    lineHeight: 1.6,
                  }}
                >
                  {selectedReport.description}
                </div>
              </div>
            )}

            {/* Token reward notice */}
            {['Admin Verified', 'In Progress', 'Work Completed', 'Resolved', 'Verified'].includes(selectedReport.status) && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  background: 'linear-gradient(135deg, #ecfdf5, #d1fae5)',
                  borderRadius: 12,
                  border: '1px solid #a7f3d0',
                  marginBottom: 22,
                }}
              >
                <Coins size={20} color="#059669" />
                <div style={{ fontSize: 13, color: '#047857', fontWeight: 600 }}>
                  Earned <strong>10 Green Tokens</strong> for this Admin-verified hostel complaint!
                </div>
              </div>
            )}

            {/* Status Progression Log / Audit Timeline */}
            <div>
              <h4
                style={{
                  color: 'var(--text-main)',
                  fontSize: 12,
                  fontWeight: 700,
                  marginBottom: 12,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <History size={14} /> Status Progression History
              </h4>

              {historyLoading ? (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: 12 }}>Loading timeline...</div>
              ) : history.length === 0 ? (
                <div
                  style={{
                    padding: '12px 16px',
                    background: '#f8fafc',
                    borderRadius: 10,
                    border: '1px solid #e2e8f0',
                    fontSize: 12,
                    color: 'var(--text-subtle)',
                  }}
                >
                  Initial report submission: {new Date(selectedReport.created_at).toLocaleString()}
                </div>
              ) : (
                <div id="status-timeline" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {history.map((h, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '10px 14px',
                        background: '#f8fafc',
                        borderRadius: 10,
                        border: '1px solid #e2e8f0',
                        fontSize: 12,
                        flexWrap: 'wrap',
                      }}
                    >
                      <span style={{ color: 'var(--text-subtle)', fontWeight: 500 }}>
                        {new Date(h.changed_at).toLocaleString()}
                      </span>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 6,
                          background: '#eff6ff',
                          color: '#2563eb',
                          fontWeight: 600,
                          fontSize: 11,
                        }}
                      >
                        {h.from_status}
                      </span>
                      <ChevronRight size={13} color="var(--text-subtle)" />
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: 6,
                          background: '#ecfdf5',
                          color: '#059669',
                          fontWeight: 600,
                          fontSize: 11,
                        }}
                      >
                        {h.to_status}
                      </span>
                      {h.reason && (
                        <span
                          style={{
                            color: 'var(--text-muted)',
                            fontSize: 12,
                            marginLeft: 'auto',
                            fontStyle: 'italic',
                          }}
                        >
                          "{h.reason}"
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

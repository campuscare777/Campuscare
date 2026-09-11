import { useState } from 'react';
import { useAuth } from './AuthContext';
import { LayoutDashboard, FileText, Coins, BarChart3, Settings, LogOut, Users, Menu, X, AlertCircle, CheckCircle, Clock, Send, Eye, ChevronRight, Upload, MapPin, Building, Layers, ArrowLeft, RefreshCw, Gift, History, TrendingUp, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } from 'recharts';
import { authAPI, reportsAPI, tokensAPI, rewardsAPI, dashboardAPI } from './api';
import { useEffect } from 'react';

function LoginPage() {
  const { login, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await login(username, password);
    if (!result.success) setError(result.error);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      <div style={{ width: 400, padding: 40, background: '#1e293b', borderRadius: 12, boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)', border: '1px solid #334155' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 56, height: 56, borderRadius: 12, background: 'linear-gradient(135deg, #22c55e, #16a34a)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <Coins size={28} color="white" />
          </div>
          <h1 style={{ color: 'white', fontSize: 24, fontWeight: 700, margin: 0 }}>Campus Green</h1>
          <p style={{ color: '#94a3b8', fontSize: 14, marginTop: 8 }}>Maintenance Reporting & Green Tokens</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%', padding: '10px 14px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
              placeholder="Enter username"
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px 14px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
              placeholder="Enter password"
            />
          </div>
          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, marginBottom: 16 }}>
              <AlertCircle size={16} color="#ef4444" />
              <span style={{ color: '#fca5a5', fontSize: 13 }}>{error}</span>
            </div>
          )}
          <button
            type="submit"
            disabled={loading || !username || !password}
            style={{ width: '100%', padding: '12px 0', background: loading || !username || !password ? '#334155' : 'linear-gradient(135deg, #22c55e, #16a34a)', color: 'white', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: loading || !username || !password ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div style={{ marginTop: 24, padding: 12, background: '#0f172a', borderRadius: 8, border: '1px solid #1e3a5f' }}>
          <p style={{ color: '#64748b', fontSize: 11, margin: 0, lineHeight: 1.6 }}>
            Demo accounts:<br />
            <span style={{ color: '#94a3b8' }}>admin / admin123</span> (Admin)<br />
            <span style={{ color: '#94a3b8' }}>maintenance1 / maint123</span> (Maintenance)<br />
            <span style={{ color: '#94a3b8' }}>student1 / student123</span> (Student)
          </p>
        </div>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon, color }) {
  const iconMap = { FileText, AlertCircle, CheckCircle, Coins, Gift, Users };
  const Icon = iconMap[icon] || FileText;
  const colorMap = { blue: '#3b82f6', green: '#22c55e', yellow: '#eab308', purple: '#a855f7', red: '#ef4444', indigo: '#6366f1' };
  const bg = colorMap[color] || '#3b82f6';
  return (
    <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155', flex: '1 1 200px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{ color: '#94a3b8', fontSize: 13 }}>{title}</span>
        <div style={{ width: 36, height: 36, borderRadius: 8, background: `${bg}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={18} color={bg} />
        </div>
      </div>
      <div style={{ color: 'white', fontSize: 28, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardAPI.get().then(res => { setData(res.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: '#94a3b8', padding: 40, textAlign: 'center' }}>Loading dashboard...</div>;
  if (!data) return <div style={{ color: '#ef4444', padding: 40, textAlign: 'center' }}>Failed to load dashboard</div>;

  const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#ef4444', '#a855f7'];

  return (
    <div>
      <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Dashboard</h2>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 32 }}>
        {data.kpis.map((kpi, i) => (
          <KPICard key={i} title={kpi.title} value={kpi.value} icon={kpi.icon} color={['blue', 'yellow', 'green', 'purple', 'red', 'indigo'][i % 6]} />
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: 'white', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Reports: Submitted vs Resolved</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={data.trend.labels.map((l, i) => ({ name: l, submitted: data.trend.submitted[i], resolved: data.trend.resolved[i] }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white' }} />
              <Area type="monotone" dataKey="submitted" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Area type="monotone" dataKey="resolved" stackId="1" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: 'white', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Reports by Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.status_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="label" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white' }} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                {data.status_distribution.map((entry, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: 'white', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Green Tokens Overview</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={data.token_summary} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={70} label={({ label, value }) => `${label}: ${value}`}>
                {data.token_summary.map((entry, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
          <h3 style={{ color: 'white', fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Recent Reports</h3>
          {data.recent_reports.map((r, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: i < data.recent_reports.length - 1 ? '1px solid #334155' : 'none' }}>
              <div>
                <div style={{ color: 'white', fontSize: 13, fontWeight: 500 }}>{r.location}</div>
                <div style={{ color: '#64748b', fontSize: 11 }}>{new Date(r.created_at).toLocaleDateString()}</div>
              </div>
              <span style={{ padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 500, background: r.status === 'Resolved' ? 'rgba(34,197,94,0.15)' : r.status === 'Submitted' ? 'rgba(59,130,246,0.15)' : r.status === 'Rejected' ? 'rgba(239,68,68,0.15)' : 'rgba(234,179,8,0.15)', color: r.status === 'Resolved' ? '#22c55e' : r.status === 'Submitted' ? '#3b82f6' : r.status === 'Rejected' ? '#ef4444' : '#eab308' }}>
                {r.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReportsPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [filter, setFilter] = useState('');
  const [formData, setFormData] = useState({ location: '', building: '', floor: '', area: '', description: '', photo: null });
  const [submitting, setSubmitting] = useState(false);
  const [statusUpdate, setStatusUpdate] = useState({ status: '', reason: '' });
  const [history, setHistory] = useState([]);

  const loadReports = () => {
    reportsAPI.list(filter || undefined).then(res => { setReports(res.data.reports); setLoading(false); });
  };

  useEffect(() => { loadReports(); }, [filter]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.photo || !formData.location) return;
    setSubmitting(true);
    const fd = new FormData();
    fd.append('photo', formData.photo);
    fd.append('location', formData.location);
    if (formData.building) fd.append('building', formData.building);
    if (formData.floor) fd.append('floor', formData.floor);
    if (formData.area) fd.append('area', formData.area);
    if (formData.description) fd.append('description', formData.description);
    try {
      await reportsAPI.create(fd);
      setShowForm(false);
      setFormData({ location: '', building: '', floor: '', area: '', description: '', photo: null });
      loadReports();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit report');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusUpdate = async (reportId) => {
    if (!statusUpdate.status) return;
    try {
      await reportsAPI.updateStatus(reportId, statusUpdate.status, statusUpdate.reason);
      setSelectedReport(null);
      setStatusUpdate({ status: '', reason: '' });
      loadReports();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const viewHistory = async (reportId) => {
    try {
      const res = await reportsAPI.getHistory(reportId);
      setHistory(res.data);
    } catch (err) {
      setHistory([]);
    }
  };

  const statusColor = (s) => ({ Submitted: '#3b82f6', Verified: '#a855f7', 'In Progress': '#eab308', Resolved: '#22c55e', Rejected: '#ef4444' }[s] || '#64748b');

  const isMaintenance = user?.role === 'maintenance' || user?.role === 'admin';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, margin: 0 }}>Reports</h2>
        <div style={{ display: 'flex', gap: 10 }}>
          {isMaintenance && (
            <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13 }}>
              <option value="">All Statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Verified">Verified</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Rejected">Rejected</option>
            </select>
          )}
          <button onClick={() => setShowForm(true)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', background: 'linear-gradient(135deg, #22c55e, #16a34a)', color: 'white', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
            <Upload size={14} /> New Report
          </button>
        </div>
      </div>

      {showForm && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, border: '1px solid #334155', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h3 style={{ color: 'white', fontSize: 16, fontWeight: 600, margin: 0 }}>Submit New Report</h3>
            <button onClick={() => setShowForm(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={18} /></button>
          </div>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Photo *</label>
                <input type="file" accept="image/*" onChange={(e) => setFormData({ ...formData, photo: e.target.files[0] })} style={{ color: '#94a3b8', fontSize: 13 }} />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Location *</label>
                <input value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} placeholder="e.g. Block A, Ground Floor" style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Building</label>
                <input value={formData.building} onChange={(e) => setFormData({ ...formData, building: e.target.value })} placeholder="e.g. Block A" style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Floor</label>
                <input value={formData.floor} onChange={(e) => setFormData({ ...formData, floor: e.target.value })} placeholder="e.g. Ground, 1st, 2nd" style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Area</label>
                <input value={formData.area} onChange={(e) => setFormData({ ...formData, area: e.target.value })} placeholder="e.g. Corridor, Washroom" style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>Description</label>
                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Describe the issue..." rows={3} style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }} />
              </div>
            </div>
            {!formData.photo && <p style={{ color: '#ef4444', fontSize: 12, marginBottom: 12 }}>Photo is required before submission</p>}
            <button type="submit" disabled={submitting || !formData.photo || !formData.location} style={{ padding: '10px 24px', background: submitting || !formData.photo || !formData.location ? '#334155' : 'linear-gradient(135deg, #22c55e, #16a34a)', color: 'white', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: submitting || !formData.photo || !formData.location ? 'not-allowed' : 'pointer' }}>
              {submitting ? 'Submitting...' : 'Submit Report'}
            </button>
          </form>
        </div>
      )}

      {selectedReport && (
        <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, border: '1px solid #334155', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <button onClick={() => { setSelectedReport(null); setHistory([]); }} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><ArrowLeft size={18} /></button>
              <h3 style={{ color: 'white', fontSize: 16, fontWeight: 600, margin: 0 }}>Report #{selectedReport.id}</h3>
              <span style={{ padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 500, background: `${statusColor(selectedReport.status)}20`, color: statusColor(selectedReport.status) }}>{selectedReport.status}</span>
            </div>
            <button onClick={() => viewHistory(selectedReport.id)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: '#94a3b8', fontSize: 12, cursor: 'pointer' }}><History size={14} /> History</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16, fontSize: 13 }}>
            <div><span style={{ color: '#64748b' }}>Location: </span><span style={{ color: 'white' }}>{selectedReport.location}</span></div>
            <div><span style={{ color: '#64748b' }}>Building: </span><span style={{ color: 'white' }}>{selectedReport.building || '-'}</span></div>
            <div><span style={{ color: '#64748b' }}>Floor: </span><span style={{ color: 'white' }}>{selectedReport.floor || '-'}</span></div>
            <div><span style={{ color: '#64748b' }}>Area: </span><span style={{ color: 'white' }}>{selectedReport.area || '-'}</span></div>
          </div>
          {selectedReport.description && <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 16 }}>{selectedReport.description}</p>}

          {history.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h4 style={{ color: 'white', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Status History</h4>
              {history.map((h, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', fontSize: 12 }}>
                  <span style={{ color: '#64748b' }}>{new Date(h.changed_at).toLocaleString()}</span>
                  <span style={{ color: statusColor(h.from_status) }}>{h.from_status}</span>
                  <ChevronRight size={12} color="#64748b" />
                  <span style={{ color: statusColor(h.to_status) }}>{h.to_status}</span>
                  {h.reason && <span style={{ color: '#ef4444', fontSize: 11 }}>({h.reason})</span>}
                </div>
              ))}
            </div>
          )}

          {isMaintenance && selectedReport.status !== 'Resolved' && selectedReport.status !== 'Rejected' && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              <div>
                <label style={{ color: '#94a3b8', fontSize: 11, display: 'block', marginBottom: 4 }}>New Status</label>
                <select value={statusUpdate.status} onChange={(e) => setStatusUpdate({ ...statusUpdate, status: e.target.value })} style={{ padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13 }}>
                  <option value="">Select...</option>
                  {selectedReport.status === 'Submitted' && <option value="Verified">Verify</option>}
                  {selectedReport.status === 'Submitted' && <option value="Rejected">Reject</option>}
                  {selectedReport.status === 'Verified' && <option value="In Progress">Start Progress</option>}
                  {selectedReport.status === 'In Progress' && <option value="Resolved">Resolve</option>}
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#94a3b8', fontSize: 11, display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                <input value={statusUpdate.reason} onChange={(e) => setStatusUpdate({ ...statusUpdate, reason: e.target.value })} style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: 'white', fontSize: 13, boxSizing: 'border-box' }} />
              </div>
              <button onClick={() => handleStatusUpdate(selectedReport.id)} disabled={!statusUpdate.status} style={{ padding: '8px 16px', background: statusUpdate.status ? '#3b82f6' : '#334155', color: 'white', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 500, cursor: statusUpdate.status ? 'pointer' : 'not-allowed' }}>Update</button>
            </div>
          )}
        </div>
      )}

      {loading ? <div style={{ color: '#94a3b8', padding: 40, textAlign: 'center' }}>Loading...</div> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {reports.map((r) => (
            <div key={r.id} onClick={() => setSelectedReport(r)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', background: '#1e293b', borderRadius: 10, border: '1px solid #334155', cursor: 'pointer', transition: 'border-color 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.borderColor = '#475569'} onMouseLeave={(e) => e.currentTarget.style.borderColor = '#334155'}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><FileText size={16} color="#64748b" /></div>
                <div>
                  <div style={{ color: 'white', fontSize: 14, fontWeight: 500 }}>Report #{r.id} - {r.location}</div>
                  <div style={{ color: '#64748b', fontSize: 12, marginTop: 2 }}>{r.building && `${r.building}, `}{r.floor && `${r.floor} Floor`}{r.area && ` - ${r.area}`}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ padding: '4px 10px', borderRadius: 12, fontSize: 11, fontWeight: 500, background: `${statusColor(r.status)}20`, color: statusColor(r.status) }}>{r.status}</span>
                <span style={{ color: '#64748b', fontSize: 11 }}>{new Date(r.created_at).toLocaleDateString()}</span>
                <ChevronRight size={16} color="#475569" />
              </div>
            </div>
          ))}
          {reports.length === 0 && <div style={{ color: '#64748b', padding: 40, textAlign: 'center', background: '#1e293b', borderRadius: 12, border: '1px solid #334155' }}>No reports found</div>}
        </div>
      )}
    </div>
  );
}

function TokensPage() {
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('balance');

  useEffect(() => {
    Promise.all([
      tokensAPI.getBalance(),
      tokensAPI.getHistory(),
      rewardsAPI.list(),
    ]).then(([b, h, r]) => {
      setBalance(b.data);
      setHistory(h.data.transactions);
      setRewards(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleRedeem = async (rewardId) => {
    try {
      const res = await rewardsAPI.redeem(rewardId);
      alert(`Redeemed: ${res.data.reward_name}. Remaining balance: ${res.data.remaining_balance} tokens`);
      const b = await tokensAPI.getBalance();
      setBalance(b.data);
      const h = await tokensAPI.getHistory();
      setHistory(h.data.transactions);
    } catch (err) {
      alert(err.response?.data?.detail || 'Redemption failed');
    }
  };

  if (loading) return <div style={{ color: '#94a3b8', padding: 40, textAlign: 'center' }}>Loading...</div>;

  const categoryColors = { canteen: '#22c55e', printing: '#3b82f6', merchandise: '#a855f7', transport: '#eab308' };

  return (
    <div>
      <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Green Tokens</h2>
      <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
        {[['balance', 'Balance'], ['history', 'History'], ['rewards', 'Rewards']].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{ padding: '8px 20px', background: tab === key ? '#22c55e' : '#1e293b', color: 'white', border: `1px solid ${tab === key ? '#22c55e' : '#334155'}`, borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>{label}</button>
        ))}
      </div>

      {tab === 'balance' && balance && (
        <div style={{ background: 'linear-gradient(135deg, #065f46, #047857)', borderRadius: 16, padding: 32, border: '1px solid #10b981', maxWidth: 400 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Coins size={24} color="#bbf7d0" />
            <span style={{ color: '#bbf7d0', fontSize: 14, fontWeight: 500 }}>Your Balance</span>
          </div>
          <div style={{ color: 'white', fontSize: 48, fontWeight: 800 }}>{balance.balance}</div>
          <div style={{ color: '#86efac', fontSize: 13, marginTop: 4 }}>Green Tokens</div>
        </div>
      )}

      {tab === 'history' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {history.map((t) => (
            <div key={t.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', background: '#1e293b', borderRadius: 10, border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: t.transaction_type === 'award' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {t.transaction_type === 'award' ? <TrendingUp size={16} color="#22c55e" /> : <TrendingDown size={16} color="#ef4444" />}
                </div>
                <div>
                  <div style={{ color: 'white', fontSize: 13, fontWeight: 500 }}>{t.transaction_type === 'award' ? 'Token Awarded' : 'Reward Redeemed'}</div>
                  <div style={{ color: '#64748b', fontSize: 11 }}>{new Date(t.created_at).toLocaleString()}</div>
                </div>
              </div>
              <span style={{ color: t.transaction_type === 'award' ? '#22c55e' : '#ef4444', fontSize: 16, fontWeight: 700 }}>
                {t.transaction_type === 'award' ? '+' : '-'}{t.amount}
              </span>
            </div>
          ))}
          {history.length === 0 && <div style={{ color: '#64748b', padding: 40, textAlign: 'center', background: '#1e293b', borderRadius: 12, border: '1px solid #334155' }}>No transactions yet</div>}
        </div>
      )}

      {tab === 'rewards' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {rewards.map((r) => (
            <div key={r.id} style={{ background: '#1e293b', borderRadius: 12, padding: 20, border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ padding: '3px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600, textTransform: 'uppercase', background: `${categoryColors[r.category] || '#64748b'}20`, color: categoryColors[r.category] || '#64748b' }}>{r.category}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#eab308', fontSize: 13, fontWeight: 600 }}><Coins size={14} /> {r.token_cost}</div>
              </div>
              <h4 style={{ color: 'white', fontSize: 15, fontWeight: 600, margin: '0 0 6px' }}>{r.name}</h4>
              <p style={{ color: '#94a3b8', fontSize: 12, margin: '0 0 16px', lineHeight: 1.5 }}>{r.description}</p>
              <button
                onClick={() => handleRedeem(r.id)}
                disabled={!balance || balance.balance < r.token_cost}
                style={{ width: '100%', padding: '10px 0', background: balance && balance.balance >= r.token_cost ? 'linear-gradient(135deg, #22c55e, #16a34a)' : '#334155', color: 'white', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: balance && balance.balance >= r.token_cost ? 'pointer' : 'not-allowed' }}
              >
                {!balance || balance.balance < r.token_cost ? `Need ${r.token_cost - (balance?.balance || 0)} more tokens` : 'Redeem'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Sidebar({ currentPage, onNavigate }) {
  const { user, logout } = useAuth();
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'tokens', label: 'Green Tokens', icon: Coins },
  ];

  return (
    <div style={{ width: 256, background: '#0f172a', borderRight: '1px solid #1e293b', display: 'flex', flexDirection: 'column', minHeight: '100vh', position: 'fixed' }}>
      <div style={{ padding: 20, borderBottom: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #22c55e, #16a34a)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Coins size={18} color="white" /></div>
          <div>
            <div style={{ color: 'white', fontSize: 15, fontWeight: 700 }}>Campus Green</div>
            <div style={{ color: '#64748b', fontSize: 11 }}>Maintenance Portal</div>
          </div>
        </div>
      </div>
      <nav style={{ padding: 12, flex: 1 }}>
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '10px 14px', marginBottom: 4,
              background: currentPage === item.id ? 'rgba(34,197,94,0.1)' : 'transparent',
              border: 'none', borderRadius: 8, cursor: 'pointer', transition: 'all 0.2s',
              color: currentPage === item.id ? '#22c55e' : '#94a3b8', fontSize: 13, fontWeight: currentPage === item.id ? 600 : 400,
              textAlign: 'left',
            }}
          >
            <item.icon size={18} /> {item.label}
          </button>
        ))}
      </nav>
      <div style={{ padding: 16, borderTop: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: '#1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Users size={14} color="#64748b" /></div>
          <div>
            <div style={{ color: 'white', fontSize: 12, fontWeight: 500 }}>{user?.full_name}</div>
            <div style={{ color: '#64748b', fontSize: 10, textTransform: 'capitalize' }}>{user?.role}</div>
          </div>
        </div>
        <button onClick={logout} style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, color: '#ef4444', fontSize: 12, cursor: 'pointer' }}><LogOut size={14} /> Sign Out</button>
      </div>
    </div>
  );
}

function AppShell() {
  const [page, setPage] = useState('dashboard');
  const pages = { dashboard: DashboardPage, reports: ReportsPage, tokens: TokensPage };
  const Page = pages[page] || DashboardPage;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      <Sidebar currentPage={page} onNavigate={setPage} />
      <main style={{ flex: 1, marginLeft: 256, padding: 32 }}>
        <Page />
      </main>
    </div>
  );
}

export default function App() {
  const { user } = useAuth();
  return user ? <AppShell /> : <LoginPage />;
}

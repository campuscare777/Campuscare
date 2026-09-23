import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import annaUnivLogo from './assets/anna_university_logo.png';
import {
  LayoutDashboard,
  FileText,
  Coins,
  BarChart3,
  Settings,
  LogOut,
  Users,
  Menu,
  X,
  AlertCircle,
  CheckCircle,
  Clock,
  Send,
  Eye,
  ChevronRight,
  Upload,
  MapPin,
  Building,
  Layers,
  ArrowLeft,
  RefreshCw,
  Gift,
  History,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Check,
  Ticket
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import { authAPI, reportsAPI, tokensAPI, rewardsAPI, dashboardAPI } from './api';
import MaintenanceReportForm from './MaintenanceReportForm';
import StaffReportsQueue from './StaffReportsQueue';
import StudentReportsView from './StudentReportsView';
import RedemptionVerification from './RedemptionVerification';

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
    <div style={{
      minHeight: '100vh',
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justify: 'center',
      background: 'radial-gradient(circle at 50% 50%, #ecfdf5 0%, #f8fafc 80%)',
      padding: 20,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative background ambient glows */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        right: '-5%',
        width: '450px',
        height: '450px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, rgba(255,255,255,0) 70%)',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '-10%',
        left: '-5%',
        width: '400px',
        height: '400px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(5, 150, 105, 0.1) 0%, rgba(255,255,255,0) 70%)',
        pointerEvents: 'none'
      }} />

      <div className="glass-card" style={{
        width: '100%',
        maxWidth: 440,
        margin: '0 auto',
        padding: '44px 40px',
        boxShadow: '0 20px 45px -10px rgba(15, 23, 42, 0.08)',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 24,
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            margin: '0 auto 18px',
          }}>
            <img
              src={annaUnivLogo}
              alt="Anna University Logo"
              style={{
                width: 92,
                height: 92,
                objectFit: 'contain',
                filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.12))'
              }}
            />
          </div>
          <h1 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
            HostelCare
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 8, fontWeight: 500 }}>
            Hostel Complaint Reporting &amp; Green Token Management
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
            />
          </div>
          <div className="form-group" style={{ marginBottom: 24 }}>
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>

          {error && (
            <div className="alert-banner alert-banner-error">
              <AlertCircle size={16} color="var(--accent-red)" style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !username || !password}
            style={{ width: '100%', padding: '14px 0', fontSize: 14, borderRadius: 12 }}
          >
            {loading ? 'Signing in...' : 'Sign In to Portal'}
          </button>
        </form>

        <div style={{
          marginTop: 32,
          padding: '18px 20px',
          background: '#f8fafc',
          borderRadius: 14,
          border: '1px solid #e2e8f0'
        }}>
          <div style={{ color: 'var(--text-subtle)', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 12 }}>
            Demo Accounts
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-main)', fontFamily: 'monospace', fontWeight: 600 }}>admin / admin123</span>
              <span className="badge badge-purple">Admin</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-main)', fontFamily: 'monospace', fontWeight: 600 }}>warden1 / warden123</span>
              <span className="badge badge-blue">Warden</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-main)', fontFamily: 'monospace', fontWeight: 600 }}>food_staff1 / food123</span>
              <span className="badge badge-amber">Food Staff</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-main)', fontFamily: 'monospace', fontWeight: 600 }}>resident1 / resident123</span>
              <span className="badge badge-emerald">Resident</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon, color }) {
  const iconMap = { FileText, AlertCircle, CheckCircle, Coins, Gift, Users };
  const Icon = iconMap[icon] || FileText;
  const colorMap = {
    blue: { hex: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    green: { hex: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
    yellow: { hex: '#d97706', bg: '#fffbeb', border: '#fde68a' },
    purple: { hex: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
    red: { hex: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
    indigo: { hex: '#4f46e5', bg: '#eef2ff', border: '#c7d2fe' },
  };
  const c = colorMap[color] || colorMap.green;
  return (
    <div className="glass-card glass-card-interactive" style={{ flex: '1 1 210px', padding: '22px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <span style={{ color: 'var(--text-subtle)', fontSize: 13, fontWeight: 600 }}>{title}</span>
        <div style={{ width: 42, height: 42, borderRadius: 12, background: c.bg, border: `1px solid ${c.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={20} color={c.hex} />
        </div>
      </div>
      <div style={{ color: 'var(--text-main)', fontSize: 32, fontWeight: 800, letterSpacing: '-1px' }}>{value}</div>
    </div>
  );
}

const CHART_TOOLTIP_STYLE = {
  background: '#ffffff',
  border: '1px solid #e2e8f0',
  borderRadius: 12,
  color: '#0f172a',
  fontSize: 12,
  boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)',
  padding: '8px 14px'
};
const CHART_GRID_COLOR = '#e2e8f0';
const CHART_AXIS_COLOR = '#64748b';
const HEX_COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#4f46e5'];

function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardAPI.get().then(res => { setData(res.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: 'var(--text-muted)', padding: 60, textAlign: 'center', fontSize: 14, fontWeight: 500 }}>Loading dashboard analytics...</div>;
  if (!data) return <div style={{ color: 'var(--accent-red)', padding: 60, textAlign: 'center', fontSize: 14, fontWeight: 600 }}>Failed to load dashboard data</div>;

  return (
    <div>
      <div style={{ marginBottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>Dashboard Overview</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>Real-time stats and hostel complaint resolution tracking</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '6px 14px', borderRadius: 999, fontSize: 12, color: '#059669', fontWeight: 600 }}>
          <div className="pulse-dot" /> Live System Active
        </div>
      </div>

      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', marginBottom: 32 }}>
        {data.kpis.map((kpi, i) => (
          <KPICard key={i} title={kpi.title} value={kpi.value} icon={kpi.icon} color={['blue', 'yellow', 'green', 'purple', 'red', 'indigo'][i % 6]} />
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-main)', fontSize: 15, fontWeight: 700, marginBottom: 20, letterSpacing: '-0.2px' }}>
            Reports Activity: Submitted vs Resolved
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data.trend.labels.map((l, i) => ({ name: l, submitted: data.trend.submitted[i], resolved: data.trend.resolved[i] }))}>
              <defs>
                <linearGradient id="gradSubmitted" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradResolved" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#059669" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_COLOR} />
              <XAxis dataKey="name" stroke={CHART_AXIS_COLOR} fontSize={11} tickLine={false} />
              <YAxis stroke={CHART_AXIS_COLOR} fontSize={11} tickLine={false} />
              <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
              <Area type="monotone" dataKey="submitted" stroke="#2563eb" fill="url(#gradSubmitted)" strokeWidth={2.5} name="Submitted" />
              <Area type="monotone" dataKey="resolved" stroke="#059669" fill="url(#gradResolved)" strokeWidth={2.5} name="Resolved" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card">
          <h3 style={{ color: 'var(--text-main)', fontSize: 15, fontWeight: 700, marginBottom: 20, letterSpacing: '-0.2px' }}>
            Reports by Status Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.status_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID_COLOR} />
              <XAxis dataKey="label" stroke={CHART_AXIS_COLOR} fontSize={11} tickLine={false} />
              <YAxis stroke={CHART_AXIS_COLOR} fontSize={11} tickLine={false} />
              <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {data.status_distribution.map((entry, i) => (
                  <Cell key={i} fill={HEX_COLORS[i % HEX_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div className="glass-card">
          <h3 style={{ color: 'var(--text-main)', fontSize: 15, fontWeight: 700, marginBottom: 20 }}>
            Green Tokens Distribution
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={data.token_summary} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={75} innerRadius={40} label={({ label, value }) => `${label}: ${value}`}>
                {data.token_summary.map((entry, i) => (
                  <Cell key={i} fill={HEX_COLORS[i % HEX_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card">
          <h3 style={{ color: 'var(--text-main)', fontSize: 15, fontWeight: 700, marginBottom: 20 }}>
            Recent Hostel Complaints
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {data.recent_reports.map((r, i) => {
              const statusStyles = {
                Resolved: { bg: '#ecfdf5', text: '#059669', border: '#a7f3d0' },
                Submitted: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
                Reported: { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe' },
                Verified: { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe' },
                'In Progress': { bg: '#fffbeb', text: '#d97706', border: '#fde68a' },
                Rejected: { bg: '#fef2f2', text: '#dc2626', border: '#fecaca' }
              }[r.status] || { bg: '#f8fafc', text: '#64748b', border: '#e2e8f0' };

              return (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'space-between',
                  padding: '12px 14px',
                  borderRadius: 10,
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  marginBottom: 6
                }}>
                  <div>
                    <div style={{ color: 'var(--text-main)', fontSize: 13, fontWeight: 700 }}>{r.location}</div>
                    <div style={{ color: 'var(--text-subtle)', fontSize: 11, marginTop: 2 }}>{new Date(r.created_at).toLocaleDateString()}</div>
                  </div>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 999,
                    fontSize: 11,
                    fontWeight: 600,
                    background: statusStyles.bg,
                    color: statusStyles.text,
                    border: `1px solid ${statusStyles.border}`
                  }}>
                    {r.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function ReportsPage() {
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const isMaintenance = ['warden', 'food_staff', 'maintenance', 'admin'].includes(user?.role);

  if (isMaintenance) {
    return <StaffReportsQueue onReportUpdated={() => setRefreshKey((k) => k + 1)} />;
  }

  return (
    <div>
      {showForm ? (
        <MaintenanceReportForm
          onCancel={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false);
            setRefreshKey((k) => k + 1);
          }}
        />
      ) : (
        <StudentReportsView
          key={refreshKey}
          onOpenReportForm={() => setShowForm(true)}
        />
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
      const code = res.data.voucher_reference || res.data.transaction_id;
      alert(`Redeemed successfully!\n\nReward: ${res.data.reward_name}\nVoucher Reference: ${code}\nRemaining Balance: ${res.data.remaining_balance} tokens\n\nShow this voucher reference to staff at the redemption counter.`);
      const b = await tokensAPI.getBalance();
      setBalance(b.data);
      const h = await tokensAPI.getHistory();
      setHistory(h.data.transactions);
    } catch (err) {
      alert(err.response?.data?.detail || 'Redemption failed');
    }
  };

  if (loading) return <div style={{ color: 'var(--text-muted)', padding: 60, textAlign: 'center', fontSize: 14, fontWeight: 500 }}>Loading Green Token details...</div>;

  const categoryColors = {
    canteen: { hex: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
    Canteen: { hex: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
    laundry: { hex: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    Laundry: { hex: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    'Hostel Stores': { hex: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
    hostel_store: { hex: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
    printing: { hex: '#d97706', bg: '#fffbeb', border: '#fde68a' },
    Printing: { hex: '#d97706', bg: '#fffbeb', border: '#fde68a' },
    merchandise: { hex: '#ec4899', bg: '#fdf2f8', border: '#fbcfe8' },
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>Green Tokens Wallet</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>Earn tokens by reporting verified hostel complaints and redeem at Canteen, Laundry, and Hostel Stores</p>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 32 }}>
        {[
          ['balance', 'Token Balance'],
          ['history', 'Transaction History'],
          ['rewards', 'Hostel Rewards Store']
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={tab === key ? 'btn btn-primary' : 'btn btn-outline'}
            style={{ fontSize: 13, padding: '10px 22px', borderRadius: 999 }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'balance' && balance && (
        <div style={{ maxWidth: 460 }}>
          <div style={{
            borderRadius: 24,
            padding: 40,
            background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
            boxShadow: '0 20px 40px -10px rgba(5, 150, 105, 0.35)',
            marginBottom: 24,
            color: 'white'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <div style={{ width: 44, height: 44, borderRadius: 14, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Coins size={24} color="#ffffff" />
              </div>
              <span style={{ fontSize: 15, fontWeight: 700, letterSpacing: '0.3px', opacity: 0.9 }}>Green Token Balance</span>
            </div>
            <div style={{ fontSize: 60, fontWeight: 900, letterSpacing: '-2px', lineHeight: 1 }}>{balance.balance}</div>
            <div style={{ fontSize: 14, marginTop: 12, fontWeight: 500, opacity: 0.9 }}>
              Tokens available for immediate redemption
            </div>
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {history.map((t) => (
            <div key={t.id} className="glass-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: t.transaction_type === 'award' ? '#ecfdf5' : '#fef2f2',
                  border: `1px solid ${t.transaction_type === 'award' ? '#a7f3d0' : '#fecaca'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'center'
                }}>
                  {t.transaction_type === 'award' ? <TrendingUp size={20} color="#059669" /> : <TrendingDown size={20} color="#dc2626" />}
                </div>
                <div>
                  <div style={{ color: 'var(--text-main)', fontSize: 15, fontWeight: 700 }}>
                    {t.transaction_type === 'award' ? 'Token Awarded (Report Verified)' : 'Reward Redeemed'}
                  </div>
                  <div style={{ color: 'var(--text-subtle)', fontSize: 12, marginTop: 3 }}>{new Date(t.created_at).toLocaleString()}</div>
                </div>
              </div>
              <span style={{ color: t.transaction_type === 'award' ? '#059669' : '#dc2626', fontSize: 22, fontWeight: 800 }}>
                {t.transaction_type === 'award' ? '+' : '-'}{t.amount}
              </span>
            </div>
          ))}
          {history.length === 0 && (
            <div className="glass-card" style={{ textAlign: 'center', padding: 60, color: 'var(--text-subtle)' }}>
              <Coins size={48} color="#cbd5e1" style={{ marginBottom: 14 }} />
              <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)' }}>No token transactions yet</p>
            </div>
          )}
        </div>
      )}

      {tab === 'rewards' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {rewards.map((r) => {
            const cat = categoryColors[r.category] || { hex: '#64748b', bg: '#f8fafc', border: '#e2e8f0' };
            const canAfford = balance && balance.balance >= r.token_cost;
            return (
              <div key={r.id} className="glass-card glass-card-interactive" style={{ padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', background: cat.bg, color: cat.hex, border: `1px solid ${cat.border}` }}>
                      {r.category}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#d97706', fontSize: 15, fontWeight: 800 }}>
                      <Coins size={16} /> {r.token_cost} Tokens
                    </div>
                  </div>
                  <h4 style={{ color: 'var(--text-main)', fontSize: 17, fontWeight: 800, margin: '0 0 6px' }}>{r.name}</h4>
                  {r.provider_location && (
                    <div style={{ color: '#059669', fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
                      📍 {r.provider_location}
                    </div>
                  )}
                  <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '0 0 20px', lineHeight: 1.6 }}>{r.description}</p>
                </div>
                <button
                  onClick={() => handleRedeem(r.id)}
                  disabled={!canAfford}
                  className={canAfford ? 'btn btn-primary' : 'btn btn-outline'}
                  style={{ width: '100%', padding: '12px 0', fontSize: 14, borderRadius: 12 }}
                >
                  {!canAfford ? `Need ${r.token_cost - (balance?.balance || 0)} more tokens` : 'Redeem Reward'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Sidebar({ currentPage, onNavigate }) {
  const { user, logout } = useAuth();
  const isStudent = user?.role === 'student';
  const isStaff = ['warden', 'maintenance', 'admin', 'food_staff'].includes(user?.role);
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'reports', label: 'Hostel Complaints', icon: FileText },
    ...(isStudent ? [{ id: 'tokens', label: 'Green Tokens', icon: Coins }] : []),
    ...(isStaff ? [{ id: 'redemptions', label: 'Redemption Verification', icon: Ticket }] : []),
  ];

  return (
    <div style={{
      width: 260,
      background: '#ffffff',
      borderRight: '1px solid #e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      position: 'fixed',
      boxShadow: '2px 0 12px rgba(15, 23, 42, 0.03)',
      zIndex: 10
    }}>
      {/* Brand Header */}
      <div style={{ padding: '28px 24px', borderBottom: '1px solid #f1f5f9' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            border: '1px solid #e2e8f0',
            padding: 4
          }}>
            <img
              src={annaUnivLogo}
              alt="Anna University"
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>
          <div>
            <div style={{ color: 'var(--text-main)', fontSize: 16, fontWeight: 800, letterSpacing: '-0.3px' }}>
              HostelCare
            </div>
            <div style={{ color: 'var(--text-subtle)', fontSize: 11, fontWeight: 600 }}>
              Resident & Staff Portal
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: '20px 14px', flex: 1 }}>
        <div style={{ color: 'var(--text-subtle)', fontSize: 11, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '1.2px', padding: '0 12px', marginBottom: 12 }}>
          Main Menu
        </div>
        {menuItems.map((item) => {
          const active = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                width: '100%',
                padding: '12px 16px',
                marginBottom: 6,
                background: active ? '#ecfdf5' : 'transparent',
                border: active ? '1px solid #a7f3d0' : '1px solid transparent',
                borderRadius: 12,
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                color: active ? '#059669' : 'var(--text-muted)',
                fontSize: 14,
                fontWeight: active ? 700 : 500,
                textAlign: 'left',
                fontFamily: 'inherit'
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.background = '#f8fafc';
                  e.currentTarget.style.color = 'var(--text-main)';
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }
              }}
            >
              <item.icon size={19} color={active ? '#059669' : '#64748b'} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* User Footer Card */}
      <div style={{ padding: '20px 14px', borderTop: '1px solid #f1f5f9' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 14px',
          background: '#f8fafc',
          borderRadius: 14,
          border: '1px solid #e2e8f0',
          marginBottom: 12
        }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            flexShrink: 0
          }}>
            <Users size={16} color="#059669" />
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ color: 'var(--text-main)', fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.full_name}
            </div>
            <div style={{ color: 'var(--text-subtle)', fontSize: 11, textTransform: 'capitalize', fontWeight: 600 }}>
              {user?.role} User
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="btn btn-danger"
          style={{ width: '100%', padding: '10px 0', fontSize: 13, borderRadius: 10, gap: 8 }}
        >
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </div>
  );
}

function AppShell() {
  const [page, setPage] = useState('dashboard');
  const pages = { dashboard: DashboardPage, reports: ReportsPage, tokens: TokensPage, redemptions: RedemptionVerification };
  const Page = pages[page] || DashboardPage;

  return (
    <div className="app-shell">
      <Sidebar currentPage={page} onNavigate={setPage} />
      <main className="main-content">
        <Page />
      </main>
    </div>
  );
}

export default function App() {
  const { user } = useAuth();
  return user ? <AppShell /> : <LoginPage />;
}

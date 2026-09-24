import React, { useState, useEffect, useCallback } from 'react';
import {
  Gift,
  Plus,
  Pencil,
  Trash2,
  X,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Coins,
  ToggleLeft,
  ToggleRight,
  ShieldAlert,
  Search,
  Tag,
  MapPin,
} from 'lucide-react';
import { rewardsAPI } from './api';

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────
const CATEGORIES = ['Canteen', 'Laundry', 'Hostel Stores'];

const CATEGORY_COLORS = {
  Canteen:        { hex: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
  Laundry:        { hex: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
  'Hostel Stores':{ hex: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
};

const FILTER_TABS = [
  { key: 'all',      label: 'All Rewards'  },
  { key: 'active',   label: 'Active'       },
  { key: 'inactive', label: 'Inactive'     },
];

const EMPTY_FORM = {
  name: '',
  description: '',
  token_cost: '',
  category: 'Canteen',
  provider_location: '',
};

// ─────────────────────────────────────────────
// Toast notification (lightweight)
// ─────────────────────────────────────────────
function Toast({ toast }) {
  if (!toast) return null;
  const isError = toast.type === 'error';
  return (
    <div
      id="reward-toast"
      style={{
        position: 'fixed',
        top: 28,
        right: 28,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '14px 20px',
        borderRadius: 14,
        background: isError ? '#fef2f2' : '#ecfdf5',
        border: `1px solid ${isError ? '#fecaca' : '#a7f3d0'}`,
        color: isError ? '#dc2626' : '#059669',
        fontSize: 14,
        fontWeight: 600,
        boxShadow: '0 8px 24px -4px rgba(0,0,0,0.12)',
        animation: 'slideInRight 0.3s cubic-bezier(0.16,1,0.3,1)',
        maxWidth: 380,
      }}
    >
      {isError
        ? <AlertCircle size={18} style={{ flexShrink: 0 }} />
        : <CheckCircle size={18} style={{ flexShrink: 0 }} />}
      <span>{toast.message}</span>
    </div>
  );
}

// ─────────────────────────────────────────────
// Reward Form Modal (create + edit)
// ─────────────────────────────────────────────
function RewardFormModal({ mode, initial, onClose, onSave, saving }) {
  const [form, setForm] = useState(initial || EMPTY_FORM);
  const [errors, setErrors] = useState({});

  const set = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const validate = () => {
    const e = {};
    if (!form.name.trim())        e.name        = 'Name is required';
    if (!form.description.trim()) e.description = 'Description is required';
    const cost = Number(form.token_cost);
    if (!form.token_cost || isNaN(cost) || cost <= 0) e.token_cost = 'Must be a positive number';
    if (!form.category)           e.category    = 'Category is required';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    onSave({
      name:              form.name.trim(),
      description:       form.description.trim(),
      token_cost:        Number(form.token_cost),
      category:          form.category,
      provider_location: form.provider_location.trim(),
    });
  };

  return (
    <div
      id="reward-form-modal-overlay"
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(15,23,42,0.45)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        id="reward-form-modal"
        style={{
          background: '#ffffff', borderRadius: 24, padding: '36px 36px 28px',
          width: '100%', maxWidth: 520, boxShadow: '0 30px 60px -10px rgba(0,0,0,0.18)',
          border: '1px solid #e2e8f0',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 42, height: 42, borderRadius: 12,
              background: '#ecfdf5', border: '1px solid #a7f3d0',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Gift size={20} color="#059669" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: 'var(--text-main)' }}>
                {mode === 'create' ? 'Add New Reward' : 'Edit Reward'}
              </h3>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--text-subtle)', marginTop: 2 }}>
                {mode === 'create' ? 'Add a reward to the catalog' : 'Update reward details'}
              </p>
            </div>
          </div>
          <button
            id="modal-close-btn"
            onClick={onClose}
            style={{
              width: 34, height: 34, borderRadius: 10, border: '1px solid #e2e8f0',
              background: '#f8fafc', cursor: 'pointer', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
            }}
          >
            <X size={16} color="#64748b" />
          </button>
        </div>

        <form onSubmit={handleSubmit} id="reward-form">
          {/* Name */}
          <div className="form-group">
            <label className="form-label">Reward Name *</label>
            <input
              id="reward-name-input"
              type="text"
              className="form-input"
              placeholder="e.g. Free Lunch Combo"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
            />
            {errors.name && <p style={{ color: 'var(--accent-red)', fontSize: 12, marginTop: 4 }}>{errors.name}</p>}
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label">Description *</label>
            <textarea
              id="reward-description-input"
              className="form-textarea"
              rows={3}
              placeholder="Brief description of what this reward includes"
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              style={{ resize: 'vertical', minHeight: 72 }}
            />
            {errors.description && <p style={{ color: 'var(--accent-red)', fontSize: 12, marginTop: 4 }}>{errors.description}</p>}
          </div>

          {/* Token Cost + Category (2-col) */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="form-group">
              <label className="form-label">Token Cost *</label>
              <input
                id="reward-token-cost-input"
                type="number"
                min={1}
                className="form-input"
                placeholder="e.g. 25"
                value={form.token_cost}
                onChange={(e) => set('token_cost', e.target.value)}
              />
              {errors.token_cost && <p style={{ color: 'var(--accent-red)', fontSize: 12, marginTop: 4 }}>{errors.token_cost}</p>}
            </div>

            <div className="form-group">
              <label className="form-label">Category *</label>
              <select
                id="reward-category-select"
                className="form-select"
                value={form.category}
                onChange={(e) => set('category', e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              {errors.category && <p style={{ color: 'var(--accent-red)', fontSize: 12, marginTop: 4 }}>{errors.category}</p>}
            </div>
          </div>

          {/* Provider Location */}
          <div className="form-group">
            <label className="form-label">Provider Location</label>
            <input
              id="reward-location-input"
              type="text"
              className="form-input"
              placeholder="e.g. Main Canteen, Ground Floor Laundry"
              value={form.provider_location}
              onChange={(e) => set('provider_location', e.target.value)}
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              style={{ flex: 1, padding: '12px 0' }}
            >
              Cancel
            </button>
            <button
              id="reward-form-submit-btn"
              type="submit"
              className="btn btn-primary"
              disabled={saving}
              style={{ flex: 2, padding: '12px 0' }}
            >
              {saving
                ? (mode === 'create' ? 'Adding...' : 'Saving...')
                : (mode === 'create' ? 'Add Reward' : 'Save Changes')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Confirm Delete Modal
// ─────────────────────────────────────────────
function ConfirmModal({ reward, onClose, onConfirm, saving }) {
  return (
    <div
      id="confirm-modal-overlay"
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(15,23,42,0.45)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        id="confirm-modal"
        style={{
          background: '#ffffff', borderRadius: 20, padding: '32px 32px 24px',
          width: '100%', maxWidth: 420, boxShadow: '0 20px 50px -10px rgba(0,0,0,0.15)',
          border: '1px solid #e2e8f0', textAlign: 'center',
        }}
      >
        <div style={{
          width: 56, height: 56, borderRadius: 16, background: '#fef2f2',
          border: '1px solid #fecaca', display: 'flex', alignItems: 'center',
          justifyContent: 'center', margin: '0 auto 20px',
        }}>
          <Trash2 size={24} color="#dc2626" />
        </div>
        <h3 style={{ margin: '0 0 8px', fontSize: 18, fontWeight: 800, color: 'var(--text-main)' }}>
          Deactivate Reward?
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '0 0 24px', lineHeight: 1.6 }}>
          <strong>"{reward.name}"</strong> will be soft-deleted and hidden from residents. You can
          re-activate it later by editing.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            id="confirm-cancel-btn"
            className="btn btn-outline"
            onClick={onClose}
            style={{ flex: 1, padding: '12px 0' }}
          >
            Cancel
          </button>
          <button
            id="confirm-delete-btn"
            className="btn btn-danger"
            onClick={onConfirm}
            disabled={saving}
            style={{ flex: 1, padding: '12px 0', fontWeight: 700 }}
          >
            {saving ? 'Deactivating...' : 'Deactivate'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Reward Row Card
// ─────────────────────────────────────────────
function RewardRow({ reward, onEdit, onDelete, onToggleActive }) {
  const cat = CATEGORY_COLORS[reward.category] || { hex: '#64748b', bg: '#f8fafc', border: '#e2e8f0' };

  return (
    <div
      className="glass-card"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto auto',
        alignItems: 'center',
        gap: 16,
        padding: '18px 22px',
        opacity: reward.is_active ? 1 : 0.65,
        transition: 'opacity 0.2s',
      }}
    >
      {/* Left: info */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
        {/* Category icon pill */}
        <div style={{
          width: 44, height: 44, borderRadius: 12, flexShrink: 0,
          background: cat.bg, border: `1px solid ${cat.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Gift size={20} color={cat.hex} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: 'var(--text-main)' }}>
              {reward.name}
            </span>
            <span style={{
              padding: '2px 10px', borderRadius: 8, fontSize: 11, fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: '0.4px',
              background: cat.bg, color: cat.hex, border: `1px solid ${cat.border}`,
            }}>
              {reward.category}
            </span>
            {!reward.is_active && (
              <span style={{
                padding: '2px 10px', borderRadius: 8, fontSize: 11, fontWeight: 700,
                background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca',
              }}>
                Inactive
              </span>
            )}
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '4px 0 6px', lineHeight: 1.5 }}>
            {reward.description}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#d97706', fontSize: 13, fontWeight: 700 }}>
              <Coins size={14} /> {reward.token_cost} tokens
            </span>
            {reward.provider_location && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#059669', fontSize: 12, fontWeight: 600 }}>
                <MapPin size={12} /> {reward.provider_location}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Middle: active toggle */}
      <button
        id={`toggle-active-btn-${reward.id}`}
        title={reward.is_active ? 'Deactivate reward' : 'Activate reward'}
        onClick={() => onToggleActive(reward)}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 6,
          color: reward.is_active ? '#059669' : '#94a3b8',
          fontSize: 12, fontWeight: 600, padding: '6px 10px',
          borderRadius: 8, transition: 'background 0.15s',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = '#f1f5f9'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
      >
        {reward.is_active
          ? <ToggleRight size={22} color="#059669" />
          : <ToggleLeft  size={22} color="#94a3b8" />}
        <span>{reward.is_active ? 'Active' : 'Inactive'}</span>
      </button>

      {/* Right: actions */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          id={`edit-reward-btn-${reward.id}`}
          title="Edit reward"
          onClick={() => onEdit(reward)}
          style={{
            width: 36, height: 36, borderRadius: 10, border: '1px solid #e2e8f0',
            background: '#f8fafc', cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#eff6ff';
            e.currentTarget.style.borderColor = '#bfdbfe';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#f8fafc';
            e.currentTarget.style.borderColor = '#e2e8f0';
          }}
        >
          <Pencil size={15} color="#2563eb" />
        </button>
        <button
          id={`delete-reward-btn-${reward.id}`}
          title="Deactivate reward"
          onClick={() => onDelete(reward)}
          disabled={!reward.is_active}
          style={{
            width: 36, height: 36, borderRadius: 10, border: '1px solid #e2e8f0',
            background: '#f8fafc', cursor: reward.is_active ? 'pointer' : 'not-allowed',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            opacity: reward.is_active ? 1 : 0.4, transition: 'all 0.15s',
          }}
          onMouseEnter={(e) => {
            if (reward.is_active) {
              e.currentTarget.style.background = '#fef2f2';
              e.currentTarget.style.borderColor = '#fecaca';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#f8fafc';
            e.currentTarget.style.borderColor = '#e2e8f0';
          }}
        >
          <Trash2 size={15} color="#dc2626" />
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────
export default function AdminRewardManagement({ userRole }) {
  const [rewards, setRewards]         = useState([]);
  const [loading, setLoading]         = useState(true);
  const [filterTab, setFilterTab]     = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [modal, setModal]             = useState(null); // null | 'create' | { mode: 'edit', reward } | { mode: 'confirm', reward }
  const [saving, setSaving]           = useState(false);
  const [toast, setToast]             = useState(null);

  // AC4 – guard at the component level
  const isAuthorized = ['admin', 'warden'].includes(userRole);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadRewards = useCallback(async () => {
    setLoading(true);
    try {
      const res = await rewardsAPI.adminList();
      setRewards(res.data);
    } catch {
      showToast('Failed to load rewards', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthorized) loadRewards();
  }, [isAuthorized, loadRewards]);

  // Filtered + searched list
  const visibleRewards = rewards.filter((r) => {
    const matchesTab =
      filterTab === 'all'      ? true :
      filterTab === 'active'   ? r.is_active :
      /* inactive */              !r.is_active;
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || r.name.toLowerCase().includes(q) || r.category.toLowerCase().includes(q);
    return matchesTab && matchesSearch;
  });

  // ── CRUD handlers ──────────────────────────
  const handleCreate = async (data) => {
    setSaving(true);
    try {
      await rewardsAPI.adminCreate(data);
      showToast(`"${data.name}" added to catalog!`);
      setModal(null);
      loadRewards();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create reward', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (rewardId, data) => {
    setSaving(true);
    try {
      await rewardsAPI.adminUpdate(rewardId, data);
      showToast('Reward updated successfully!');
      setModal(null);
      loadRewards();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update reward', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (reward) => {
    setSaving(true);
    try {
      await rewardsAPI.adminDelete(reward.id);
      showToast(`"${reward.name}" deactivated.`);
      setModal(null);
      loadRewards();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to deactivate reward', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (reward) => {
    setSaving(true);
    try {
      await rewardsAPI.adminUpdate(reward.id, { is_active: !reward.is_active });
      showToast(reward.is_active ? `"${reward.name}" deactivated.` : `"${reward.name}" activated!`);
      loadRewards();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update reward', 'error');
    } finally {
      setSaving(false);
    }
  };

  // ─────────────────────────────────────────
  // AC4: Unauthorized access guard
  // ─────────────────────────────────────────
  if (!isAuthorized) {
    return (
      <div id="reward-access-denied" style={{ textAlign: 'center', padding: '80px 20px' }}>
        <div style={{
          width: 72, height: 72, borderRadius: 20, background: '#fef2f2',
          border: '1px solid #fecaca', display: 'flex', alignItems: 'center',
          justifyContent: 'center', margin: '0 auto 20px',
        }}>
          <ShieldAlert size={32} color="#dc2626" />
        </div>
        <h2 style={{ color: 'var(--text-main)', fontWeight: 800, fontSize: 22, margin: '0 0 10px' }}>
          Access Denied
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, maxWidth: 380, margin: '0 auto' }}>
          You do not have permission to manage rewards. Only admins and wardens can access this page.
        </p>
      </div>
    );
  }

  // ─────────────────────────────────────────
  // Statistics bar
  // ─────────────────────────────────────────
  const totalActive   = rewards.filter((r) => r.is_active).length;
  const totalInactive = rewards.filter((r) => !r.is_active).length;
  const totalAll      = rewards.length;

  const statCards = [
    { label: 'Total Rewards',    value: totalAll,      color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    { label: 'Active',           value: totalActive,   color: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
    { label: 'Inactive',         value: totalInactive, color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
  ];

  return (
    <div id="admin-reward-management">
      <Toast toast={toast} />

      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
            Reward Catalog Management
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>
            Create, edit, and manage the hostel reward catalog available to residents
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            id="refresh-rewards-btn"
            className="btn btn-outline"
            onClick={loadRewards}
            disabled={loading}
            style={{ padding: '10px 18px', fontSize: 13 }}
          >
            <RefreshCw size={15} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
          <button
            id="add-reward-btn"
            className="btn btn-primary"
            onClick={() => setModal({ mode: 'create' })}
            style={{ padding: '10px 22px', fontSize: 13 }}
          >
            <Plus size={16} /> Add New Reward
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        {statCards.map((s) => (
          <div key={s.label} className="glass-card" style={{ flex: '1 1 150px', padding: '18px 22px' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-subtle)', marginBottom: 8 }}>{s.label}</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: s.color, letterSpacing: '-1px' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Filters & Search */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14, marginBottom: 20, flexWrap: 'wrap' }}>
        {/* Tab filters */}
        <div style={{ display: 'flex', gap: 8 }}>
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              id={`filter-tab-${tab.key}`}
              className={filterTab === tab.key ? 'btn btn-primary' : 'btn btn-outline'}
              onClick={() => setFilterTab(tab.key)}
              style={{ fontSize: 12, padding: '8px 18px', borderRadius: 999 }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search box */}
        <div style={{ position: 'relative', maxWidth: 260, flex: '1 1 200px' }}>
          <Search size={15} color="#94a3b8" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input
            id="reward-search-input"
            type="text"
            className="form-input"
            placeholder="Search rewards..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: 36, fontSize: 13 }}
          />
        </div>
      </div>

      {/* Reward list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)', fontSize: 14, fontWeight: 500 }}>
          Loading reward catalog...
        </div>
      ) : visibleRewards.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <Gift size={48} color="#cbd5e1" style={{ marginBottom: 14 }} />
          <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)', margin: '0 0 6px' }}>
            {rewards.length === 0 ? 'No rewards yet' : 'No rewards match your filters'}
          </p>
          <p style={{ color: 'var(--text-subtle)', fontSize: 13 }}>
            {rewards.length === 0
              ? 'Click "Add New Reward" to populate the catalog.'
              : 'Try changing your search or filter.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {visibleRewards.map((r) => (
            <RewardRow
              key={r.id}
              reward={r}
              onEdit={(reward) => setModal({ mode: 'edit', reward })}
              onDelete={(reward) => setModal({ mode: 'confirm', reward })}
              onToggleActive={handleToggleActive}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {modal?.mode === 'create' && (
        <RewardFormModal
          mode="create"
          initial={EMPTY_FORM}
          onClose={() => setModal(null)}
          onSave={handleCreate}
          saving={saving}
        />
      )}
      {modal?.mode === 'edit' && (
        <RewardFormModal
          mode="edit"
          initial={{
            name:              modal.reward.name,
            description:       modal.reward.description,
            token_cost:        String(modal.reward.token_cost),
            category:          modal.reward.category,
            provider_location: modal.reward.provider_location || '',
          }}
          onClose={() => setModal(null)}
          onSave={(data) => handleUpdate(modal.reward.id, data)}
          saving={saving}
        />
      )}
      {modal?.mode === 'confirm' && (
        <ConfirmModal
          reward={modal.reward}
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.reward)}
          saving={saving}
        />
      )}
    </div>
  );
}

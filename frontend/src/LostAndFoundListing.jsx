import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { lostAndFoundAPI } from './api';
import {
  Search,
  Filter,
  Plus,
  Tag,
  MapPin,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  Package,
  Eye,
  HandHelping,
  X,
  RefreshCw,
  Sparkles,
  Info,
  ShieldCheck,
  Building,
  Check,
  ChevronDown,
  Layers,
  ArrowRight
} from 'lucide-react';

const ITEM_CATEGORIES = [
  'All',
  'Electronics',
  'Clothing',
  'Keys',
  'Books / Stationery',
  'Wallet / Purse',
  'Jewellery / Accessories',
  'ID Card / Documents',
  'Sports Equipment',
  'Food Items',
  'Documents',
  'Other',
];

const HOSTEL_TYPES = [
  'All',
  'Boys Hostel',
  'Girls Hostel',
  'NRI Hostel',
  'Common Areas',
];

export default function LostAndFoundListing({ onReportMissing, onReportFound }) {
  const { user } = useAuth();

  // ── States ────────────────────────────────────────────────────────────────
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedHostelType, setSelectedHostelType] = useState('All');
  const [selectedReportType, setSelectedReportType] = useState('All'); // 'All' | 'Lost' | 'Found'
  const [hideClosed, setHideClosed] = useState(true); // AC4: Hide closed by default for active listings
  const [onlyMyReports, setOnlyMyReports] = useState(false);

  // Detail Modal & Claim Modal States
  const [selectedReport, setSelectedReport] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [claimNotes, setClaimNotes] = useState('');
  const [proofDetails, setProofDetails] = useState('');
  const [claimSubmitting, setClaimSubmitting] = useState(false);
  const [claimSuccessMsg, setClaimSuccessMsg] = useState('');
  const [claimErrorMsg, setClaimErrorMsg] = useState('');

  // Staff action states
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [selectedNewStatus, setSelectedNewStatus] = useState('');
  const [statusReason, setStatusReason] = useState('');

  const isStaff = ['admin', 'warden', 'staff', 'hostel_staff', 'maintenance', 'food_staff'].includes(user?.role);

  // ── Fetch Reports ─────────────────────────────────────────────────────────
  const fetchReports = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (selectedReportType !== 'All') params.report_type = selectedReportType;
      if (selectedCategory !== 'All') params.item_category = selectedCategory;
      if (selectedHostelType !== 'All') params.hostel_type = selectedHostelType;
      if (hideClosed) params.hide_closed = true;
      if (onlyMyReports) params.my_reports = true;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await lostAndFoundAPI.list(params);
      setReports(res.data.reports || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load lost and found listings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [selectedCategory, selectedHostelType, selectedReportType, hideClosed, onlyMyReports]);

  // Handle Search Debounce / Submit
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchReports();
  };

  // ── Open Details ──────────────────────────────────────────────────────────
  const handleOpenDetails = async (report) => {
    setSelectedReport(report);
    setLoadingDetails(true);
    setClaimSuccessMsg('');
    setClaimErrorMsg('');
    try {
      const res = await lostAndFoundAPI.get(report.item_report_id);
      setSelectedReport(res.data);
    } catch (err) {
      console.error('Failed to fetch full report details:', err);
    } finally {
      setLoadingDetails(false);
    }
  };

  // ── Claim Submission (AC5) ────────────────────────────────────────────────
  const handleClaimSubmit = async (e) => {
    e.preventDefault();
    if (!selectedReport) return;
    setClaimSubmitting(true);
    setClaimErrorMsg('');
    setClaimSuccessMsg('');

    try {
      const res = await lostAndFoundAPI.claim(selectedReport.item_report_id, {
        claim_notes: claimNotes,
        proof_details: proofDetails,
      });

      setClaimSuccessMsg('Claim request submitted successfully! Hostel staff will verify your details.');
      setSelectedReport(res.data);
      // Update item in local list
      setReports((prev) =>
        prev.map((r) => (r.item_report_id === res.data.item_report_id ? res.data : r))
      );
      setTimeout(() => {
        setShowClaimModal(false);
        setClaimNotes('');
        setProofDetails('');
      }, 1800);
    } catch (err) {
      setClaimErrorMsg(err.response?.data?.detail || 'Failed to submit claim request. Please try again.');
    } finally {
      setClaimSubmitting(false);
    }
  };

  // ── Staff Status Update ───────────────────────────────────────────────────
  const handleStaffStatusUpdate = async (newStatus) => {
    if (!selectedReport || !newStatus) return;
    setStatusUpdating(true);
    try {
      const res = await lostAndFoundAPI.updateStatus(selectedReport.item_report_id, {
        status: newStatus,
        assigned_staff: user?.full_name || user?.username,
        reason: statusReason || `Status changed to ${newStatus} by staff`,
      });
      setSelectedReport(res.data);
      setReports((prev) =>
        prev.map((r) => (r.item_report_id === res.data.item_report_id ? res.data : r))
      );
      setStatusReason('');
      setSelectedNewStatus('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setStatusUpdating(false);
    }
  };

  // Status Styling Helper
  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'returned' || s === 'closed') {
      return { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1', label: status, isClosed: true };
    }
    if (s === 'claim requested') {
      return { bg: '#fffbeb', color: '#d97706', border: '#fde68a', label: 'Claim Requested', isClosed: false };
    }
    if (s === 'verified' || s === 'published') {
      return { bg: '#ecfdf5', color: '#059669', border: '#a7f3d0', label: status, isClosed: false };
    }
    if (s === 'received by staff' || s === 'under review') {
      return { bg: '#eff6ff', color: '#2563eb', border: '#bfdbfe', label: status, isClosed: false };
    }
    return { bg: '#f8fafc', color: '#64748b', border: '#e2e8f0', label: status || 'Submitted', isClosed: false };
  };

  // Counts summary
  const totalActive = reports.filter((r) => r.status !== 'Closed' && r.status !== 'Returned').length;
  const totalLost = reports.filter((r) => r.report_type === 'Lost').length;
  const totalFound = reports.filter((r) => r.report_type === 'Found').length;

  return (
    <div className="lost-and-found-page" id="lost-and-found-container" style={{ paddingBottom: 60 }}>
      {/* ── Top Header Banner ────────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 16,
          marginBottom: 28,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 700,
                background: '#ecfdf5',
                color: '#059669',
                border: '1px solid #a7f3d0',
              }}
            >
              <Sparkles size={14} /> HostelCare Community Hub
            </span>
          </div>
          <h2
            id="lost-and-found-title"
            style={{
              color: 'var(--text-main)',
              fontSize: 28,
              fontWeight: 800,
              margin: 0,
              letterSpacing: '-0.5px',
            }}
          >
            Lost &amp; Found Directory
          </h2>
          <p
            id="lost-and-found-subtitle"
            style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 6, fontWeight: 500 }}
          >
            Browse active lost and found items across hostels, identify your missing belongings, or help return found items.
          </p>
        </div>

        {/* Action Buttons: Report Missing / Found */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            id="btn-report-found"
            onClick={onReportFound}
            className="btn btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              borderRadius: 12,
              fontWeight: 600,
            }}
          >
            <HandHelping size={18} color="#059669" />
            Report Found Item
          </button>
          <button
            id="btn-report-missing"
            onClick={onReportMissing}
            className="btn btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 20px',
              borderRadius: 12,
              fontWeight: 600,
            }}
          >
            <Plus size={18} />
            Report Missing Item
          </button>
        </div>
      </div>

      {/* ── Filter & Search Control Panel (AC2) ────────────────────────────── */}
      <div
        className="glass-card"
        id="filter-control-panel"
        style={{
          padding: 20,
          marginBottom: 24,
          background: '#ffffff',
          borderRadius: 18,
          border: '1px solid #e2e8f0',
        }}
      >
        {/* Search row & Report Type Toggle */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'center',
            flexWrap: 'wrap',
            marginBottom: 16,
          }}
        >
          {/* Search Form */}
          <form
            onSubmit={handleSearchSubmit}
            style={{ flex: '1 1 320px', display: 'flex', position: 'relative' }}
          >
            <Search
              size={18}
              color="var(--text-subtle)"
              style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              id="search-input"
              type="text"
              className="form-input"
              style={{
                width: '100%',
                paddingLeft: 42,
                paddingRight: 80,
                borderRadius: 12,
                fontSize: 14,
              }}
              placeholder="Search items by name, description, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              type="submit"
              id="search-submit-btn"
              className="btn btn-primary"
              style={{
                position: 'absolute',
                right: 4,
                top: 4,
                bottom: 4,
                padding: '0 14px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              Search
            </button>
          </form>

          {/* Report Type Filter Tabs (AC2) */}
          <div
            id="report-type-filter"
            style={{
              display: 'flex',
              background: '#f1f5f9',
              padding: 4,
              borderRadius: 12,
              gap: 4,
            }}
          >
            {[
              { id: 'All', label: 'All Items' },
              { id: 'Lost', label: '🔍 Lost Items' },
              { id: 'Found', label: '🎁 Found Items' },
            ].map((tab) => {
              const active = selectedReportType === tab.id;
              return (
                <button
                  key={tab.id}
                  id={`filter-type-${tab.id.toLowerCase()}`}
                  onClick={() => setSelectedReportType(tab.id)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 9,
                    border: 'none',
                    background: active ? '#ffffff' : 'transparent',
                    color: active ? '#0f172a' : 'var(--text-muted)',
                    fontWeight: active ? 700 : 500,
                    fontSize: 13,
                    cursor: 'pointer',
                    boxShadow: active ? '0 2px 6px rgba(0,0,0,0.06)' : 'none',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Dropdowns Row: Category, Hostel Type, Status/Closed Toggle (AC2, AC4) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
            paddingTop: 12,
            borderTop: '1px solid #f1f5f9',
          }}
        >
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            {/* Category Dropdown Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <label
                htmlFor="category-select"
                style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-subtle)' }}
              >
                Category:
              </label>
              <select
                id="category-select"
                className="form-input"
                style={{
                  padding: '7px 12px',
                  borderRadius: 10,
                  fontSize: 13,
                  width: 'auto',
                  minWidth: 160,
                }}
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {ITEM_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat === 'All' ? 'All Categories' : cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Hostel Type Dropdown Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <label
                htmlFor="hostel-type-select"
                style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-subtle)' }}
              >
                Hostel:
              </label>
              <select
                id="hostel-type-select"
                className="form-input"
                style={{
                  padding: '7px 12px',
                  borderRadius: 10,
                  fontSize: 13,
                  width: 'auto',
                  minWidth: 150,
                }}
                value={selectedHostelType}
                onChange={(e) => setSelectedHostelType(e.target.value)}
              >
                {HOSTEL_TYPES.map((h) => (
                  <option key={h} value={h}>
                    {h === 'All' ? 'All Hostels' : h}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Toggles: Active Only / Hide Closed (AC4) & My Reports */}
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <label
              id="hide-closed-toggle-label"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--text-main)',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <input
                id="hide-closed-checkbox"
                type="checkbox"
                checked={hideClosed}
                onChange={(e) => setHideClosed(e.target.checked)}
                style={{ accentColor: '#059669', width: 16, height: 16 }}
              />
              Active Items Only (Hide Closed/Returned)
            </label>

            <label
              id="my-reports-toggle-label"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--text-main)',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <input
                id="my-reports-checkbox"
                type="checkbox"
                checked={onlyMyReports}
                onChange={(e) => setOnlyMyReports(e.target.checked)}
                style={{ accentColor: '#059669', width: 16, height: 16 }}
              />
              My Reports Only
            </label>

            <button
              id="refresh-listing-btn"
              onClick={fetchReports}
              title="Refresh listings"
              className="btn btn-outline"
              style={{ padding: '6px 10px', borderRadius: 8 }}
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* ── Active Items Grid / Listing (AC1, AC4) ─────────────────────────── */}
      {loading ? (
        <div
          id="loading-spinner-state"
          style={{
            padding: 80,
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: 15,
            fontWeight: 500,
          }}
        >
          <div className="pulse-dot" style={{ margin: '0 auto 16px', width: 14, height: 14 }} />
          Loading lost and found item reports...
        </div>
      ) : error ? (
        <div
          id="error-banner"
          className="alert-banner alert-banner-error"
          style={{ marginBottom: 20 }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      ) : reports.length === 0 ? (
        <div
          id="empty-reports-state"
          className="glass-card"
          style={{
            textAlign: 'center',
            padding: '70px 20px',
            borderRadius: 20,
            background: '#ffffff',
            border: '1px dashed #cbd5e1',
          }}
        >
          <div
            style={{
              width: 60,
              height: 60,
              borderRadius: 20,
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <Package size={28} color="#059669" />
          </div>
          <h3 style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 700, margin: '0 0 8px' }}>
            No Matching Item Reports Found
          </h3>
          <p
            style={{
              color: 'var(--text-muted)',
              fontSize: 14,
              maxWidth: 420,
              margin: '0 auto 20px',
            }}
          >
            {hideClosed
              ? 'There are currently no active reports matching your filter criteria.'
              : 'No lost or found item reports match the selected filters.'}
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
            <button
              onClick={() => {
                setSelectedCategory('All');
                setSelectedHostelType('All');
                setSelectedReportType('All');
                setSearchQuery('');
                setOnlyMyReports(false);
                setHideClosed(false);
              }}
              className="btn btn-outline"
              style={{ fontSize: 13, borderRadius: 10 }}
            >
              Reset Filters
            </button>
            <button
              onClick={onReportMissing}
              className="btn btn-primary"
              style={{ fontSize: 13, borderRadius: 10 }}
            >
              Report a Missing Item
            </button>
          </div>
        </div>
      ) : (
        <div
          id="reports-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))',
            gap: 20,
          }}
        >
          {reports.map((item) => {
            const isLost = item.report_type === 'Lost';
            const badge = getStatusBadge(item.status);
            const isClosed = badge.isClosed;

            return (
              <div
                key={item.item_report_id}
                id={`report-card-${item.item_report_id}`}
                className="glass-card glass-card-interactive"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: 0,
                  borderRadius: 18,
                  overflow: 'hidden',
                  background: isClosed ? '#fafafa' : '#ffffff',
                  border: isClosed ? '1px solid #e2e8f0' : '1px solid #e2e8f0',
                  opacity: isClosed ? 0.85 : 1,
                  boxShadow: '0 4px 15px -2px rgba(15, 23, 42, 0.04)',
                }}
                onClick={() => handleOpenDetails(item)}
              >
                {/* Top Image / Banner area (AC3) */}
                <div
                  style={{
                    height: 150,
                    width: '100%',
                    background: item.image_reference
                      ? '#0f172a'
                      : isLost
                      ? 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)'
                      : 'linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {item.image_reference ? (
                    <img
                      src={`http://localhost:8000/${item.image_reference}`}
                      alt={item.item_name}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 6,
                        color: isLost ? '#dc2626' : '#059669',
                      }}
                    >
                      <Package size={40} strokeWidth={1.5} />
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase' }}>
                        {item.item_category}
                      </span>
                    </div>
                  )}

                  {/* Report Type Pill (Lost / Found) */}
                  <div
                    id={`report-type-badge-${item.item_report_id}`}
                    style={{
                      position: 'absolute',
                      top: 12,
                      left: 12,
                      padding: '4px 12px',
                      borderRadius: 999,
                      fontSize: 11,
                      fontWeight: 800,
                      letterSpacing: '0.4px',
                      textTransform: 'uppercase',
                      background: isLost ? '#dc2626' : '#059669',
                      color: '#ffffff',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                    }}
                  >
                    {isLost ? '🔍 Lost' : '🎁 Found'}
                  </div>

                  {/* Status Badge (AC4: marked as closed or active status) */}
                  <div
                    id={`status-badge-${item.item_report_id}`}
                    style={{
                      position: 'absolute',
                      top: 12,
                      right: 12,
                      padding: '4px 10px',
                      borderRadius: 8,
                      fontSize: 11,
                      fontWeight: 700,
                      background: badge.bg,
                      color: badge.color,
                      border: `1px solid ${badge.border}`,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
                    }}
                  >
                    {badge.label}
                  </div>

                  {/* Item Reference ID tag */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: 8,
                      right: 12,
                      padding: '2px 8px',
                      borderRadius: 6,
                      fontSize: 10,
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      background: 'rgba(0,0,0,0.6)',
                      color: '#ffffff',
                    }}
                  >
                    #LNF-{item.item_report_id}
                  </div>
                </div>

                {/* Card Content Body */}
                <div style={{ padding: '18px 20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <h4
                        id={`item-name-${item.item_report_id}`}
                        style={{
                          color: 'var(--text-main)',
                          fontSize: 16,
                          fontWeight: 800,
                          margin: '0 0 4px',
                          letterSpacing: '-0.2px',
                          lineHeight: 1.3,
                        }}
                      >
                        {item.item_name}
                      </h4>
                    </div>

                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: 6,
                        fontSize: 11,
                        fontWeight: 600,
                        background: '#f1f5f9',
                        color: '#475569',
                        marginBottom: 10,
                      }}
                    >
                      {item.item_category}
                    </span>
                  </div>

                  {/* Description preview */}
                  <p
                    style={{
                      color: 'var(--text-muted)',
                      fontSize: 13,
                      margin: '0 0 14px',
                      lineHeight: 1.5,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      flex: 1,
                    }}
                  >
                    {item.description || item.identifying_details || 'No detailed description provided.'}
                  </p>

                  {/* Location and Date details */}
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6,
                      fontSize: 12,
                      color: 'var(--text-subtle)',
                      paddingTop: 12,
                      borderTop: '1px solid #f1f5f9',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <MapPin size={14} color="#059669" />
                      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                        {item.location} {item.hostel_type ? `(${item.hostel_type})` : ''}
                      </span>
                    </div>
                    {item.date_lost_or_found && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Calendar size={14} color="#64748b" />
                        <span>{new Date(item.date_lost_or_found).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Action Footer */}
                <div
                  style={{
                    padding: '12px 20px',
                    background: '#f8fafc',
                    borderTop: '1px solid #f1f5f9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      color: 'var(--text-subtle)',
                      fontWeight: 500,
                    }}
                  >
                    Reported by: <strong>{item.reporter_name || 'Resident'}</strong>
                  </span>

                  <button
                    id={`view-details-btn-${item.item_report_id}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenDetails(item);
                    }}
                    className="btn btn-outline"
                    style={{
                      fontSize: 12,
                      padding: '6px 14px',
                      borderRadius: 8,
                      fontWeight: 600,
                      gap: 4,
                    }}
                  >
                    View Details <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── AC3: Item Details Modal / View ─────────────────────────────────── */}
      {selectedReport && (
        <div
          id="item-details-modal"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
          onClick={() => setSelectedReport(null)}
        >
          <div
            className="glass-card"
            style={{
              background: '#ffffff',
              borderRadius: 24,
              maxWidth: 680,
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 0,
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '24px 28px',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span
                  style={{
                    padding: '4px 12px',
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    background: selectedReport.report_type === 'Lost' ? '#dc2626' : '#059669',
                    color: '#ffffff',
                  }}
                >
                  {selectedReport.report_type} Item Report
                </span>
                <span style={{ fontSize: 13, color: 'var(--text-subtle)', fontWeight: 600 }}>
                  #LNF-{selectedReport.item_report_id}
                </span>
              </div>

              <button
                id="close-details-modal-btn"
                onClick={() => setSelectedReport(null)}
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: '50%',
                  width: 34,
                  height: 34,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px 28px' }}>
              {/* Image Preview (AC3) */}
              {selectedReport.image_reference && (
                <div
                  id="details-image-container"
                  style={{
                    width: '100%',
                    height: 240,
                    borderRadius: 16,
                    overflow: 'hidden',
                    background: '#0f172a',
                    marginBottom: 20,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <img
                    id="details-item-image"
                    src={`http://localhost:8000/${selectedReport.image_reference}`}
                    alt={selectedReport.item_name}
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                </div>
              )}

              {/* Title & Status */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                <div>
                  <h3
                    id="details-item-name"
                    style={{
                      fontSize: 22,
                      fontWeight: 800,
                      color: 'var(--text-main)',
                      margin: '0 0 6px',
                      letterSpacing: '-0.3px',
                    }}
                  >
                    {selectedReport.item_name}
                  </h3>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '3px 10px',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 600,
                      background: '#ecfdf5',
                      color: '#059669',
                      border: '1px solid #a7f3d0',
                    }}
                  >
                    {selectedReport.item_category}
                  </span>
                </div>

                {/* Status Badge */}
                <div
                  id="details-status-badge"
                  style={{
                    padding: '6px 14px',
                    borderRadius: 10,
                    fontSize: 12,
                    fontWeight: 700,
                    background: getStatusBadge(selectedReport.status).bg,
                    color: getStatusBadge(selectedReport.status).color,
                    border: `1px solid ${getStatusBadge(selectedReport.status).border}`,
                  }}
                >
                  Status: {selectedReport.status}
                </div>
              </div>

              {/* Details Key-Value Grid (AC3) */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 16,
                  padding: 18,
                  background: '#f8fafc',
                  borderRadius: 14,
                  border: '1px solid #e2e8f0',
                  marginBottom: 20,
                  fontSize: 13,
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    📍 Location:
                  </span>
                  <span id="details-location" style={{ color: 'var(--text-main)', fontWeight: 700 }}>
                    {selectedReport.location}
                  </span>
                </div>

                <div>
                  <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    🏢 Hostel Type:
                  </span>
                  <span id="details-hostel-type" style={{ color: 'var(--text-main)', fontWeight: 700 }}>
                    {selectedReport.hostel_type || 'General Campus'}
                  </span>
                </div>

                <div>
                  <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    📅 Date {selectedReport.report_type === 'Lost' ? 'Lost' : 'Found'}:
                  </span>
                  <span id="details-date" style={{ color: 'var(--text-main)', fontWeight: 700 }}>
                    {selectedReport.date_lost_or_found
                      ? new Date(selectedReport.date_lost_or_found).toLocaleDateString()
                      : 'Not specified'}
                  </span>
                </div>

                <div>
                  <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    👤 Reported By:
                  </span>
                  <span id="details-reporter" style={{ color: 'var(--text-main)', fontWeight: 700 }}>
                    {selectedReport.reporter_name || 'Resident'}
                  </span>
                </div>

                {selectedReport.assigned_staff && (
                  <div>
                    <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                      🛡️ Assigned Staff / Custodian:
                    </span>
                    <span style={{ color: '#059669', fontWeight: 700 }}>
                      {selectedReport.assigned_staff}
                    </span>
                  </div>
                )}

                {selectedReport.closed_at && (
                  <div>
                    <span style={{ color: 'var(--text-subtle)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                      🔒 Closure Date:
                    </span>
                    <span style={{ color: '#475569', fontWeight: 700 }}>
                      {new Date(selectedReport.closed_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              {/* Description Section (AC3) */}
              <div style={{ marginBottom: 18 }}>
                <h4 style={{ color: 'var(--text-main)', fontSize: 14, fontWeight: 700, marginBottom: 6 }}>
                  Item Description:
                </h4>
                <p
                  id="details-description"
                  style={{
                    color: 'var(--text-muted)',
                    fontSize: 14,
                    lineHeight: 1.6,
                    margin: 0,
                    background: '#ffffff',
                    padding: 14,
                    borderRadius: 10,
                    border: '1px solid #e2e8f0',
                  }}
                >
                  {selectedReport.description || 'No detailed description provided.'}
                </p>
              </div>

              {/* Identifying Details Section (AC3) */}
              {selectedReport.identifying_details && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ color: 'var(--text-main)', fontSize: 14, fontWeight: 700, marginBottom: 6 }}>
                    Identifying Details &amp; Unique Marks:
                  </h4>
                  <div
                    id="details-identifying-details"
                    style={{
                      padding: 12,
                      borderRadius: 10,
                      background: '#ecfdf5',
                      border: '1px solid #a7f3d0',
                      color: '#065f46',
                      fontSize: 13,
                      lineHeight: 1.5,
                    }}
                  >
                    {selectedReport.identifying_details}
                  </div>
                </div>
              )}

              {/* Success Notification in Details */}
              {claimSuccessMsg && (
                <div className="alert-banner alert-banner-success" style={{ marginBottom: 16 }}>
                  <CheckCircle2 size={16} />
                  <span>{claimSuccessMsg}</span>
                </div>
              )}

              {/* Staff Management Controls (Staff/Admin) */}
              {isStaff && (
                <div
                  style={{
                    padding: 16,
                    background: '#f8fafc',
                    borderRadius: 14,
                    border: '1px solid #cbd5e1',
                    marginBottom: 16,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <ShieldCheck size={18} color="#2563eb" />
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>
                      Staff Workflow Actions
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                    {['Received by Staff', 'Published', 'Verified', 'Returned', 'Closed'].map((st) => (
                      <button
                        key={st}
                        onClick={() => handleStaffStatusUpdate(st)}
                        disabled={statusUpdating || selectedReport.status === st}
                        className={selectedReport.status === st ? 'btn btn-primary' : 'btn btn-outline'}
                        style={{ fontSize: 12, padding: '6px 12px', borderRadius: 8 }}
                      >
                        {statusUpdating ? 'Updating...' : `Mark ${st}`}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Resident Claim Button (AC5) */}
              {selectedReport.status !== 'Returned' && selectedReport.status !== 'Closed' && (
                <div style={{ display: 'flex', gap: 12, marginTop: 24, justifyContent: 'flex-end' }}>
                  <button
                    id="btn-claim-item"
                    onClick={() => setShowClaimModal(true)}
                    className="btn btn-primary"
                    style={{
                      padding: '12px 24px',
                      borderRadius: 12,
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <HandHelping size={18} />
                    {selectedReport.report_type === 'Found'
                      ? 'Claim This Found Item'
                      : 'I Found This Missing Item'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── AC5: Claim Submission Modal ────────────────────────────────────── */}
      {showClaimModal && selectedReport && (
        <div
          id="claim-modal"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1100,
            padding: 20,
          }}
          onClick={() => setShowClaimModal(false)}
        >
          <div
            className="glass-card"
            style={{
              background: '#ffffff',
              borderRadius: 24,
              maxWidth: 520,
              width: '100%',
              padding: '32px 30px',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.3)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: '#ecfdf5',
                    border: '1px solid #a7f3d0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <HandHelping size={20} color="#059669" />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
                  Submit Claim Request
                </h3>
              </div>
              <button
                id="close-claim-modal-btn"
                onClick={() => setShowClaimModal(false)}
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: '50%',
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                <X size={16} />
              </button>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20, lineHeight: 1.5 }}>
              Claiming: <strong>{selectedReport.item_name}</strong> (#{selectedReport.item_report_id}).
              Provide proof of ownership or verification details for hostel staff.
            </p>

            {claimErrorMsg && (
              <div className="alert-banner alert-banner-error" style={{ marginBottom: 16 }}>
                <AlertCircle size={16} />
                <span>{claimErrorMsg}</span>
              </div>
            )}

            {claimSuccessMsg && (
              <div className="alert-banner alert-banner-success" style={{ marginBottom: 16 }}>
                <CheckCircle2 size={16} />
                <span>{claimSuccessMsg}</span>
              </div>
            )}

            <form onSubmit={handleClaimSubmit}>
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label className="form-label" htmlFor="claim-proof-details">
                  Proof of Ownership / Identifying Marks <span style={{ color: '#dc2626' }}>*</span>
                </label>
                <textarea
                  id="claim-proof-details"
                  className="form-input"
                  rows={3}
                  required
                  placeholder="Describe unique features, serial numbers, password patterns, or contents to verify ownership..."
                  value={proofDetails}
                  onChange={(e) => setProofDetails(e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 24 }}>
                <label className="form-label" htmlFor="claim-notes">
                  Additional Notes / Contact Information
                </label>
                <input
                  id="claim-notes"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Phone number, hostel room number, or handover time preference"
                  value={claimNotes}
                  onChange={(e) => setClaimNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowClaimModal(false)}
                  className="btn btn-outline"
                  style={{ padding: '10px 18px', borderRadius: 10 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="submit-claim-btn"
                  disabled={claimSubmitting || !proofDetails.trim()}
                  className="btn btn-primary"
                  style={{ padding: '10px 22px', borderRadius: 10, fontWeight: 700 }}
                >
                  {claimSubmitting ? 'Submitting Claim...' : 'Send Claim to Staff'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

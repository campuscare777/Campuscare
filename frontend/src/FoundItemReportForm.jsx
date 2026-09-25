import { useState } from 'react';
import {
  Upload, MapPin, AlertCircle, CheckCircle, X,
  Send, Package, Home, Camera, Tag,
} from 'lucide-react';
import { lostAndFoundAPI } from './api';

// ── Constants ────────────────────────────────────────────────────────────────

const ITEM_CATEGORIES = [
  'Electronics',
  'Clothing',
  'Keys',
  'Books / Stationery',
  'Wallet / Purse',
  'Jewellery / Accessories',
  'ID Card / Documents',
  'Sports Equipment',
  'Food Items',
  'Other',
];

const HOSTEL_LOCATIONS = [
  'Boys Hostel – Block A',
  'Boys Hostel – Block B',
  'Boys Hostel – Block C',
  'Boys Hostel – Block D',
  'Girls Hostel – Block E',
  'Girls Hostel – Block F',
  'Girls Hostel – Block G',
  'NRI Hostel – Wing A',
  'NRI Hostel – Wing B',
  'Common Area / Corridor',
  'Dining Hall / Mess',
  'Library / Study Room',
  'Gymnasium',
  'Entrance / Gate',
  'Other',
];

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * FoundItemReportForm
 *
 * Implements HOSTELCARE-F004-UI-002 – Found Item Report Form.
 *
 * Acceptance Criteria:
 *   AC1 – Form renders item-details and found-location fields on load.
 *   AC2 – Valid submission calls the backend API and creates a report.
 *   AC3 – Optional image upload; reference stored with the report.
 *   AC4 – Info banner explains staff-receipt workflow (status update flow).
 *
 * @param {() => void}         onCancel   Navigate back without saving.
 * @param {(report) => void}   onSuccess  Called after successful submission.
 */
export default function FoundItemReportForm({ onCancel, onSuccess }) {
  // ── Form state ──────────────────────────────────────────────────────────────
  const [formData, setFormData] = useState({
    report_type: 'Found',
    item_category: '',
    item_name: '',
    location: '',
    description: '',
    hostel_type: '',
    date_lost_or_found: new Date().toISOString().split('T')[0],
    identifying_details: '',
  });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successReport, setSuccessReport] = useState(null);

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrorMessage('');
  };

  /** AC3 – store image file & generate a local preview URL. */
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setErrorMessage('Image must be smaller than 5 MB.');
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setErrorMessage('');
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  /** AC1 – validate required item-details and found-location fields. */
  const validate = () => {
    if (!formData.item_category) return 'Please select an item category.';
    if (!formData.item_name.trim()) return 'Please enter the item name.';
    if (!formData.location) return 'Please select where you found the item.';
    if (!formData.date_lost_or_found) return 'Please enter the date you found the item.';
    return null;
  };

  /** AC2 – build FormData and POST to the backend; AC3 – attach image. */
  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setErrorMessage(validationError); return; }

    setSubmitting(true);
    setErrorMessage('');

    try {
      const fd = new FormData();
      fd.append('report_type', formData.report_type);
      fd.append('item_category', formData.item_category);
      fd.append('item_name', formData.item_name.trim());
      fd.append('location', formData.location);
      if (formData.description.trim()) fd.append('description', formData.description.trim());
      if (formData.hostel_type)        fd.append('hostel_type', formData.hostel_type);
      fd.append('date_lost_or_found', formData.date_lost_or_found);
      if (formData.identifying_details.trim())
        fd.append('identifying_details', formData.identifying_details.trim());
      if (imageFile) fd.append('image', imageFile); // AC3

      const response = await lostAndFoundAPI.create(fd);
      setSuccessReport(response.data);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Submission failed. Please try again.';
      setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const handleReportAnother = () => {
    setSuccessReport(null);
    setFormData({
      report_type: 'Found',
      item_category: '',
      item_name: '',
      location: '',
      description: '',
      hostel_type: '',
      date_lost_or_found: new Date().toISOString().split('T')[0],
      identifying_details: '',
    });
    setImageFile(null);
    setImagePreview(null);
  };

  // ── Success Screen ───────────────────────────────────────────────────────────

  if (successReport) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: 'var(--bg-canvas)',
      }}>
        <div style={{
          maxWidth: 520,
          width: '100%',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-card)',
          padding: '48px 40px',
          textAlign: 'center',
          boxShadow: 'var(--shadow-card)',
        }}>
          <div style={{
            width: 72, height: 72,
            background: 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 24px',
            boxShadow: '0 8px 24px -4px rgba(16,185,129,0.4)',
          }}>
            <CheckCircle size={36} color="#fff" />
          </div>

          <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-main)', marginBottom: 10 }}>
            Found-Item Report Submitted!
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 28, lineHeight: 1.6 }}>
            Your report has been saved. Hostel staff will review it and work
            to reunite the item with its rightful owner.
          </p>

          <div style={{
            background: 'var(--primary-light)',
            border: '1px solid var(--primary-border)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
            marginBottom: 28,
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700, color: 'var(--primary-emerald)',
              textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 6,
            }}>
              Report Reference
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: 18, fontWeight: 700, color: 'var(--text-main)' }}>
              #{String(successReport.item_report_id ?? successReport.id ?? '').padStart(6, '0')}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              {successReport.item_name} &middot; {successReport.item_category}
            </div>
          </div>

          <div style={{ marginBottom: 28 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 14px',
              background: 'var(--accent-amber-bg)',
              border: '1px solid var(--accent-amber-border)',
              borderRadius: 20,
              fontSize: 12, fontWeight: 600, color: 'var(--accent-amber)',
            }}>
              Status: {successReport.status ?? 'Submitted'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              id="found-item-report-another-btn"
              type="button"
              className="btn btn-secondary"
              onClick={handleReportAnother}
              style={{ padding: '10px 22px', borderRadius: 10 }}
            >
              Report Another
            </button>
            <button
              id="found-item-done-btn"
              type="button"
              className="btn btn-primary"
              onClick={() => onSuccess && onSuccess(successReport)}
              style={{ padding: '10px 22px', borderRadius: 10 }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Form ─────────────────────────────────────────────────────────────────────

  return (
    <div style={{ padding: '24px 0', background: 'var(--bg-canvas)', minHeight: '100vh' }}>
      {/* Back navigation */}
      <div style={{ maxWidth: 720, margin: '0 auto 16px', padding: '0 24px' }}>
        <button
          id="found-item-back-btn"
          type="button"
          onClick={onCancel}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            display: 'inline-flex', alignItems: 'center', gap: 6,
            color: 'var(--text-muted)', fontSize: 14, fontWeight: 500, padding: '6px 0',
          }}
        >
          &larr; Back
        </button>
      </div>

      <div style={{ maxWidth: 720, margin: '0 auto', padding: '0 24px' }}>

        {/* Hero header */}
        <div style={{
          background: 'var(--primary-gradient)',
          borderRadius: 'var(--radius-xl)',
          padding: '28px 32px',
          marginBottom: 24,
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', right: -20, top: -20,
            width: 130, height: 130, borderRadius: '50%',
            background: 'rgba(255,255,255,0.08)',
          }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, position: 'relative' }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: 'rgba(255,255,255,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Package size={26} />
            </div>
            <div>
              <h1 id="found-item-form-title" style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>
                Report a Found Item
              </h1>
              <p style={{ fontSize: 13, opacity: 0.85, margin: '4px 0 0' }}>
                Help us return this item to its owner &middot; HOSTELCARE-F004-UI-002
              </p>
            </div>
          </div>
        </div>

        {/* Form card */}
        <div style={{
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-card)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-card)',
        }}>
          <form id="found-item-report-form" onSubmit={handleSubmit}>

            {/* Section 1 – Item Details (AC1) */}
            <div style={{ padding: '28px 32px', borderBottom: '1px solid var(--border-subtle)' }}>
              <SectionHeader
                icon={<Tag size={16} color="var(--primary-emerald)" />}
                iconBg="var(--primary-light)"
                label="Item Details"
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" htmlFor="item-category">
                    Item Category <span style={{ color: 'var(--accent-red)' }}>*</span>
                  </label>
                  <select
                    id="item-category"
                    className="form-input"
                    value={formData.item_category}
                    onChange={(e) => handleChange('item_category', e.target.value)}
                  >
                    <option value="">Select category</option>
                    {ITEM_CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" htmlFor="item-name">
                    Item Name <span style={{ color: 'var(--accent-red)' }}>*</span>
                  </label>
                  <input
                    id="item-name"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Blue Samsung phone"
                    value={formData.item_name}
                    onChange={(e) => handleChange('item_name', e.target.value)}
                    maxLength={100}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginTop: 18, marginBottom: 0 }}>
                <label className="form-label" htmlFor="identifying-details">
                  Identifying Details
                  <span style={{ color: 'var(--text-light)', fontWeight: 400, marginLeft: 6 }}>
                    (colour, brand, markings&hellip;)
                  </span>
                </label>
                <input
                  id="identifying-details"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Blue cover, cracked screen protector"
                  value={formData.identifying_details}
                  onChange={(e) => handleChange('identifying_details', e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginTop: 18, marginBottom: 0 }}>
                <label className="form-label" htmlFor="item-description">
                  Additional Description
                </label>
                <textarea
                  id="item-description"
                  className="form-input"
                  rows={3}
                  placeholder="Any details that may help identify the owner&hellip;"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  style={{ resize: 'vertical', minHeight: 80 }}
                />
              </div>
            </div>

            {/* Section 2 – Found Location (AC1) */}
            <div style={{ padding: '28px 32px', borderBottom: '1px solid var(--border-subtle)' }}>
              <SectionHeader
                icon={<MapPin size={16} color="var(--accent-blue)" />}
                iconBg="var(--accent-blue-bg)"
                label="Found Location"
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" htmlFor="found-location">
                    Where was it found? <span style={{ color: 'var(--accent-red)' }}>*</span>
                  </label>
                  <select
                    id="found-location"
                    className="form-input"
                    value={formData.location}
                    onChange={(e) => handleChange('location', e.target.value)}
                  >
                    <option value="">Select location</option>
                    {HOSTEL_LOCATIONS.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" htmlFor="date-found">
                    Date Found <span style={{ color: 'var(--accent-red)' }}>*</span>
                  </label>
                  <input
                    id="date-found"
                    type="date"
                    className="form-input"
                    value={formData.date_lost_or_found}
                    max={new Date().toISOString().split('T')[0]}
                    onChange={(e) => handleChange('date_lost_or_found', e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginTop: 18, marginBottom: 0 }}>
                <label className="form-label" htmlFor="hostel-type">
                  Hostel Type
                  <span style={{ color: 'var(--text-light)', fontWeight: 400, marginLeft: 6 }}>
                    (optional)
                  </span>
                </label>
                <select
                  id="hostel-type"
                  className="form-input"
                  value={formData.hostel_type}
                  onChange={(e) => handleChange('hostel_type', e.target.value)}
                >
                  <option value="">Select hostel</option>
                  <option value="Boys Hostel">Boys Hostel</option>
                  <option value="Girls Hostel">Girls Hostel</option>
                  <option value="NRI Hostel">NRI Hostel</option>
                </select>
              </div>
            </div>

            {/* Section 3 – Photo Upload (AC3) */}
            <div style={{ padding: '28px 32px', borderBottom: '1px solid var(--border-subtle)' }}>
              <SectionHeader
                icon={<Camera size={16} color="var(--accent-purple)" />}
                iconBg="var(--accent-purple-bg)"
                label={
                  <span>
                    Item Photo
                    <span style={{ color: 'var(--text-light)', fontSize: 13, fontWeight: 400, marginLeft: 8 }}>
                      optional &ndash; max 5 MB
                    </span>
                  </span>
                }
              />

              {imagePreview ? (
                <div style={{ position: 'relative', display: 'inline-block' }}>
                  <img
                    src={imagePreview}
                    alt="Item preview"
                    style={{
                      width: '100%', maxWidth: 320, height: 200,
                      objectFit: 'cover', borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-card)',
                    }}
                  />
                  <button
                    id="found-item-remove-image-btn"
                    type="button"
                    onClick={handleRemoveImage}
                    title="Remove image"
                    style={{
                      position: 'absolute', top: 8, right: 8,
                      background: 'rgba(0,0,0,0.6)', border: 'none',
                      borderRadius: '50%', width: 28, height: 28,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      cursor: 'pointer', color: '#fff',
                    }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <label
                  id="found-item-upload-label"
                  htmlFor="item-image-upload"
                  style={{
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center', gap: 10,
                    border: '2px dashed var(--border-card)',
                    borderRadius: 'var(--radius-md)',
                    padding: '32px 24px', cursor: 'pointer',
                    background: 'var(--bg-card)',
                    transition: 'border-color 0.2s, background 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--primary-emerald)';
                    e.currentTarget.style.background = 'var(--primary-light)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-card)';
                    e.currentTarget.style.background = 'var(--bg-card)';
                  }}
                >
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'var(--primary-light)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Upload size={22} color="var(--primary-emerald)" />
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                      Click to upload a photo
                    </p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
                      PNG, JPG, WEBP &ndash; max 5 MB
                    </p>
                  </div>
                  <input
                    id="item-image-upload"
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={handleImageChange}
                  />
                </label>
              )}
            </div>

            {/* Error banner */}
            {errorMessage && (
              <div style={{ padding: '0 32px' }}>
                <div className="alert-banner alert-banner-error" style={{ marginTop: 20 }}>
                  <AlertCircle size={16} color="var(--accent-red)" style={{ flexShrink: 0 }} />
                  <span>{errorMessage}</span>
                </div>
              </div>
            )}

            {/* Footer actions */}
            <div style={{
              padding: '24px 32px',
              display: 'flex', gap: 12, justifyContent: 'flex-end',
              background: 'var(--bg-canvas)',
              borderTop: '1px solid var(--border-subtle)',
            }}>
              <button
                id="found-item-cancel-btn"
                type="button"
                className="btn btn-secondary"
                onClick={onCancel}
                style={{ padding: '11px 24px', borderRadius: 10 }}
              >
                Cancel
              </button>
              <button
                id="found-item-submit-btn"
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
                style={{
                  padding: '11px 28px', borderRadius: 10,
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                }}
              >
                {submitting ? 'Submitting\u2026' : (
                  <>
                    <Send size={15} />
                    Submit Found Report
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* AC4 – staff handover info banner: when staff confirm receipt, status is updated */}
        <div style={{
          marginTop: 16,
          padding: '14px 20px',
          background: 'var(--accent-blue-bg)',
          border: '1px solid var(--accent-blue-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'flex-start', gap: 10,
        }}>
          <Home size={16} color="var(--accent-blue)" style={{ marginTop: 1, flexShrink: 0 }} />
          <p style={{ fontSize: 13, color: 'var(--accent-blue)', margin: 0, lineHeight: 1.5 }}>
            <strong>What happens next?</strong> Please hand the item to the hostel warden or
            security desk. Once received, authorized staff will update the report status to{' '}
            <em>Received by Staff</em> and reach out to potential owners.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function SectionHeader({ icon, iconBg, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
      <div style={{
        width: 34, height: 34, borderRadius: 10,
        background: iconBg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <h2 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
        {label}
      </h2>
    </div>
  );
}

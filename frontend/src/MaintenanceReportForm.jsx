import { useState, useEffect } from 'react';
import { Upload, MapPin, AlertCircle, CheckCircle, X, Send, FileText, Home } from 'lucide-react';
import { reportsAPI } from './api';

const HOSTEL_TYPES = ['Boys Hostel', 'Girls Hostel', 'NRI Hostel'];

const HOSTEL_LOCATIONS = {
  'Boys Hostel':  { blocks: ['Block A', 'Block B', 'Block C', 'Block D'], floors: ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor'], areas: ['Lobby', 'Corridor', 'Washroom', 'Common Room', 'Dining Area', 'Gym', 'Study Room'] },
  'Girls Hostel': { blocks: ['Block E', 'Block F', 'Block G'], floors: ['Ground Floor', '1st Floor', '2nd Floor', '3rd Floor'], areas: ['Lobby', 'Corridor', 'Washroom', 'Common Room', 'Dining Area', 'Study Room'] },
  'NRI Hostel':   { blocks: ['NRI Wing A', 'NRI Wing B'], floors: ['Ground Floor', '1st Floor', '2nd Floor'], areas: ['Lobby', 'Corridor', 'Washroom', 'Common Room', 'Dining Area'] },
};

const COMPLAINT_CATEGORIES = [
  'Electrical', 'Plumbing', 'Cleanliness', 'Food/Mess',
  'Internet/Network', 'Furniture', 'Pest Control', 'Water Supply', 'Other',
];

export default function MaintenanceReportForm({ onCancel, onSuccess }) {
  const [hostelConfig, setHostelConfig] = useState(HOSTEL_LOCATIONS);
  const [formData, setFormData] = useState({
    hostel_type: '',
    building: '',
    floor: '',
    area: '',
    category: '',
    description: '',
    photo: null,
  });
  const [photoPreview, setPhotoPreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [confirmedReport, setConfirmedReport] = useState(null);

  useEffect(() => {
    // Try to fetch hostel config from backend; fall back to defaults
    reportsAPI.getHostelConfig()
      .then((res) => {
        if (res.data?.hostel_locations) {
          const locs = res.data.hostel_locations;
          const normalized = {};
          Object.keys(locs).forEach((key) => {
            normalized[key] = {
              blocks: locs[key].blocks || [],
              floors: locs[key].floors || [],
              areas: locs[key].areas || locs[key].common_areas || [],
              common_areas: locs[key].common_areas || locs[key].areas || [],
            };
          });
          setHostelConfig(normalized);
        }
      })
      .catch(() => {});
  }, []);

  const selectedHostel = formData.hostel_type ? (hostelConfig[formData.hostel_type] || null) : null;
  const blocks = selectedHostel?.blocks || [];
  const floors = selectedHostel?.floors || [];
  const areas = selectedHostel?.areas || selectedHostel?.common_areas || [];

  const handleHostelTypeChange = (e) => {
    const val = e.target.value;
    setFormData((prev) => ({
      ...prev,
      hostel_type: val,
      building: '',
      floor: '',
      area: '',
    }));
    setErrorMessage('');
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData((prev) => ({ ...prev, photo: file }));
      setPhotoPreview(URL.createObjectURL(file));
      setErrorMessage('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!formData.hostel_type) {
      setErrorMessage('Please select a hostel type.');
      return;
    }
    if (!formData.category) {
      setErrorMessage('Please select a complaint category.');
      return;
    }

    const location = [formData.building, formData.area].filter(Boolean).join(', ') || formData.hostel_type;

    setSubmitting(true);
    const payload = new FormData();
    payload.append('hostel_type', formData.hostel_type);
    payload.append('location', location);
    payload.append('category', formData.category);
    if (formData.building) payload.append('building', formData.building);
    if (formData.floor)    payload.append('floor', formData.floor);
    if (formData.area)     payload.append('area', formData.area);
    if (formData.description) payload.append('description', formData.description);
    if (formData.photo)    payload.append('photo', formData.photo);

    try {
      const res = await reportsAPI.create(payload);
      setConfirmedReport(res.data);
      if (onSuccess) onSuccess(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to submit complaint. Please check required fields.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setConfirmedReport(null);
    setFormData({ hostel_type: '', building: '', floor: '', area: '', category: '', description: '', photo: null });
    setPhotoPreview(null);
    setErrorMessage('');
  };

  // ─── Success screen ────────────────────────────────────────────────
  if (confirmedReport) {
    return (
      <div className="glass-card" style={{ maxWidth: 640, margin: '0 auto 28px', padding: 36, textAlign: 'center' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#ecfdf5', border: '1px solid #a7f3d0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckCircle size={36} color="#059669" />
        </div>
        <h3 style={{ color: 'var(--text-main)', fontSize: 22, fontWeight: 800, margin: '0 0 8px' }}>Complaint Submitted Successfully!</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: '0 0 24px' }}>Your hostel complaint has been registered and sent to the warden for verification.</p>

        <div style={{ background: '#f8fafc', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0', marginBottom: 28, textAlign: 'left' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 14, marginBottom: 14, borderBottom: '1px solid #e2e8f0' }}>
            <span style={{ color: 'var(--text-subtle)', fontSize: 13, fontWeight: 600 }}>Tracking ID</span>
            <span style={{ color: '#059669', fontSize: 20, fontWeight: 800 }}>#{confirmedReport.id}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, fontSize: 13, marginBottom: 16 }}>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Status</span>
              <span className="badge badge-emerald">{confirmedReport.status || 'Submitted'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Submitted At</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{new Date(confirmedReport.created_at).toLocaleString()}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Hostel</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{confirmedReport.hostel_type}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Category</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{confirmedReport.category}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Location</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{confirmedReport.location}</span>
            </div>
          </div>

          {photoPreview && (
            <div style={{ marginTop: 14 }}>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 8, fontWeight: 700, textTransform: 'uppercase' }}>Attached Photo</span>
              <img src={photoPreview} alt="Issue photo" style={{ width: '100%', maxHeight: 200, objectFit: 'cover', borderRadius: 12, border: '1px solid #e2e8f0' }} />
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 14 }}>
          <button onClick={resetForm} className="btn btn-outline" style={{ flex: 1, padding: '12px 0' }}>
            Submit Another Complaint
          </button>
          {onCancel && (
            <button onClick={onCancel} className="btn btn-primary" style={{ flex: 1, padding: '12px 0' }}>
              Done / View Complaints
            </button>
          )}
        </div>
      </div>
    );
  }

  // ─── Form ────────────────────────────────────────────────────────────
  return (
    <div className="glass-card" style={{ marginBottom: 28, padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 14, background: '#ecfdf5', border: '1px solid #a7f3d0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Home size={22} color="#059669" />
          </div>
          <div>
            <h3 style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 800, margin: 0 }}>Report Hostel Complaint</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: '2px 0 0', fontWeight: 500 }}>Fill in the hostel details and describe the issue. Photo is optional but recommended.</p>
          </div>
        </div>
        {onCancel && (
          <button onClick={onCancel} style={{ background: '#f1f5f9', border: 'none', color: '#64748b', cursor: 'pointer', padding: 8, borderRadius: 10 }}>
            <X size={18} />
          </button>
        )}
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner-error">
          <AlertCircle size={18} color="#dc2626" style={{ flexShrink: 0 }} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>

          {/* Step 1: Hostel Type */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Hostel <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <select
              id="hostel-type-select"
              value={formData.hostel_type}
              onChange={handleHostelTypeChange}
              className="form-select"
            >
              <option value="">-- Select Hostel --</option>
              {HOSTEL_TYPES.map((h) => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>

          {/* Complaint Category */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Complaint Category <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <select
              id="complaint-category-select"
              value={formData.category}
              onChange={(e) => { setFormData({ ...formData, category: e.target.value }); setErrorMessage(''); }}
              className="form-select"
            >
              <option value="">-- Select Category --</option>
              {COMPLAINT_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Step 2: Block (depends on hostel type) */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Block / Wing</label>
            <select
              id="hostel-block-select"
              value={formData.building}
              onChange={(e) => setFormData({ ...formData, building: e.target.value })}
              className="form-select"
              disabled={!selectedHostel}
            >
              <option value="">{selectedHostel ? '-- Select Block / Wing --' : '-- First Select Hostel --'}</option>
              {blocks.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>

          {/* Step 3: Floor */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Floor</label>
            <select
              id="hostel-floor-select"
              value={formData.floor}
              onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
              className="form-select"
              disabled={!selectedHostel}
            >
              <option value="">{selectedHostel ? '-- Select Floor --' : '-- First Select Hostel --'}</option>
              {floors.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>

          {/* Area */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Area / Room</label>
            <select
              id="hostel-area-select"
              value={formData.area}
              onChange={(e) => setFormData({ ...formData, area: e.target.value })}
              className="form-select"
              disabled={!selectedHostel}
            >
              <option value="">{selectedHostel ? '-- Select Area / Room --' : '-- First Select Hostel --'}</option>
              {areas.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>

          {/* Photo (optional) */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Attach Photo <span style={{ color: '#64748b', fontWeight: 500 }}>(optional, recommended)</span>
            </label>
            <input
              type="file"
              id="complaint-photo-input"
              accept="image/*"
              onChange={handlePhotoChange}
              className="form-input"
              style={{ padding: '9px 14px' }}
            />
          </div>

          {/* Description */}
          <div style={{ gridColumn: '1 / -1' }} className="form-group">
            <label className="form-label">Description / Details (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the issue in detail — what happened, how long it has been occurring, etc."
              rows={3}
              className="form-textarea"
            />
          </div>
        </div>

        {/* Photo Preview */}
        {photoPreview && (
          <div style={{ marginBottom: 20, padding: 14, background: '#f8fafc', borderRadius: 14, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 16 }}>
            <img src={photoPreview} alt="Selected preview" style={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 10, border: '1px solid #cbd5e1' }} />
            <div>
              <span style={{ color: 'var(--text-main)', fontSize: 13, fontWeight: 700, display: 'block' }}>{formData.photo.name}</span>
              <span style={{ color: 'var(--text-subtle)', fontSize: 11, fontWeight: 500 }}>{(formData.photo.size / 1024).toFixed(1)} KB</span>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12 }}>
          {onCancel && (
            <button type="button" onClick={onCancel} className="btn btn-outline">
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={submitting}
            id="submit-complaint-btn"
            className="btn btn-primary"
            style={{ padding: '12px 28px' }}
          >
            <Send size={16} />
            {submitting ? 'Submitting...' : 'Submit Complaint'}
          </button>
        </div>
      </form>
    </div>
  );
}


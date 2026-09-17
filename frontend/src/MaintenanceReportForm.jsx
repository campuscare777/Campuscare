import { useState, useEffect } from 'react';
import { Upload, MapPin, Building, Layers, AlertCircle, CheckCircle, X, Send, FileText, ArrowLeft, Image as ImageIcon } from 'lucide-react';
import { reportsAPI } from './api';

const DEFAULT_LOCATIONS = [
  { id: 'library', name: 'Library', building: 'Main Library Block', zone: 'Academic Zone' },
  { id: 'hostel_a', name: 'Hostel Block A', building: 'Hostel Block A', zone: 'Residential Zone' },
  { id: 'canteen', name: 'Canteen / Cafeteria', building: 'Student Center', zone: 'Dining Zone' },
  { id: 'auditorium', name: 'Main Auditorium', building: 'Auditorium Block', zone: 'Central Zone' },
  { id: 'parking_lot', name: 'Parking Lot', building: 'Parking Complex', zone: 'Outer Zone' },
  { id: 'sports_complex', name: 'Sports Complex', building: 'Sports Center', zone: 'Recreation Zone' },
  { id: 'science_block', name: 'Science Block', building: 'Block S', zone: 'Academic Zone' },
  { id: 'admin_building', name: 'Admin Building', building: 'Admin Block', zone: 'Admin Zone' },
];

export default function MaintenanceReportForm({ onCancel, onSuccess }) {
  const [locations, setLocations] = useState(DEFAULT_LOCATIONS);
  const [formData, setFormData] = useState({
    location: '',
    building: '',
    floor: '',
    area: '',
    description: '',
    photo: null,
  });
  const [photoPreview, setPhotoPreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [confirmedReport, setConfirmedReport] = useState(null);

  useEffect(() => {
    reportsAPI
      .getLocations()
      .then((res) => {
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          setLocations(res.data);
        }
      })
      .catch(() => {
        // Fallback to DEFAULT_LOCATIONS
      });
  }, []);

  const handleLocationChange = (e) => {
    const locName = e.target.value;
    const foundLoc = locations.find((l) => l.name === locName);
    setFormData((prev) => ({
      ...prev,
      location: locName,
      building: foundLoc ? foundLoc.building : prev.building,
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

    if (!formData.photo || !formData.location.trim()) {
      setErrorMessage('Both a photo and a location are required to submit a maintenance report.');
      return;
    }

    setSubmitting(true);
    const payload = new FormData();
    payload.append('photo', formData.photo);
    payload.append('location', formData.location);
    if (formData.building) payload.append('building', formData.building);
    if (formData.floor) payload.append('floor', formData.floor);
    if (formData.area) payload.append('area', formData.area);
    if (formData.description) payload.append('description', formData.description);

    try {
      const res = await reportsAPI.create(payload);
      setConfirmedReport(res.data);
      if (onSuccess) onSuccess(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === 'string' ? detail : 'Failed to submit report. Please check required fields.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setConfirmedReport(null);
    setFormData({ location: '', building: '', floor: '', area: '', description: '', photo: null });
    setPhotoPreview(null);
    setErrorMessage('');
  };

  if (confirmedReport) {
    return (
      <div className="glass-card" style={{ maxWidth: 640, margin: '0 auto 28px', padding: 36, textAlign: 'center' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#ecfdf5', border: '1px solid #a7f3d0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckCircle size={36} color="#059669" />
        </div>
        <h3 style={{ color: 'var(--text-main)', fontSize: 22, fontWeight: 800, margin: '0 0 8px' }}>Report Submitted Successfully!</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: '0 0 24px' }}>Your maintenance issue report has been registered and sent for verification.</p>

        <div style={{ background: '#f8fafc', borderRadius: 16, padding: 24, border: '1px solid #e2e8f0', marginBottom: 28, textAlign: 'left' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 14, marginBottom: 14, borderBottom: '1px solid #e2e8f0' }}>
            <span style={{ color: 'var(--text-subtle)', fontSize: 13, fontWeight: 600 }}>Tracking ID</span>
            <span style={{ color: '#059669', fontSize: 20, fontWeight: 800 }}>#{confirmedReport.id}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, fontSize: 13, marginBottom: 16 }}>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Status</span>
              <span className="badge badge-emerald">{confirmedReport.status || 'Reported'}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Submitted At</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{new Date(confirmedReport.created_at).toLocaleString()}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Location</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{confirmedReport.location}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: 11, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Building</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{confirmedReport.building || 'N/A'}</span>
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
            Submit Another Report
          </button>
          {onCancel && (
            <button onClick={onCancel} className="btn btn-primary" style={{ flex: 1, padding: '12px 0' }}>
              Done / View Reports
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ marginBottom: 28, padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 14, background: '#ecfdf5', border: '1px solid #a7f3d0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={22} color="#059669" />
          </div>
          <div>
            <h3 style={{ color: 'var(--text-main)', fontSize: 18, fontWeight: 800, margin: 0 }}>Report Campus Maintenance & Cleanliness Issue</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: '2px 0 0', fontWeight: 500 }}>Upload a photo and details to report an issue on campus</p>
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
          {/* Location Selection */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Issue Location <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <select
              value={formData.location}
              onChange={handleLocationChange}
              className="form-select"
            >
              <option value="">-- Select Campus Location --</option>
              {locations.map((loc) => (
                <option key={loc.id || loc.name} value={loc.name}>
                  {loc.name} ({loc.building})
                </option>
              ))}
            </select>
          </div>

          {/* Building */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Building / Block (Optional)</label>
            <input
              type="text"
              value={formData.building}
              onChange={(e) => setFormData({ ...formData, building: e.target.value })}
              placeholder="e.g. Block A"
              className="form-input"
            />
          </div>

          {/* Floor & Area */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Floor</label>
              <input
                type="text"
                value={formData.floor}
                onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                placeholder="e.g. 1st Floor"
                className="form-input"
              />
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Area</label>
              <input
                type="text"
                value={formData.area}
                onChange={(e) => setFormData({ ...formData, area: e.target.value })}
                placeholder="e.g. Washroom"
                className="form-input"
              />
            </div>
          </div>

          {/* Photo File Upload Box */}
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Upload Photo <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handlePhotoChange}
              className="form-input"
              style={{ padding: '9px 14px' }}
            />
          </div>

          {/* Description */}
          <div style={{ gridColumn: '1 / -1' }} className="form-group">
            <label className="form-label">Description / Issue Details (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the issue, cleanliness concern or maintenance requirement in detail..."
              rows={3}
              className="form-textarea"
            />
          </div>
        </div>

        {/* Photo Preview Card */}
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
            disabled={submitting || !formData.photo || !formData.location}
            className="btn btn-primary"
            style={{ padding: '12px 28px' }}
          >
            <Send size={16} />
            {submitting ? 'Submitting Report...' : 'Submit Report'}
          </button>
        </div>
      </form>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Upload, MapPin, Building, Layers, AlertCircle, CheckCircle, X, Send, FileText, ArrowLeft } from 'lucide-react';
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

    // Business Rule 4: Validation - cannot submit unless both photo and location are present
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
      <div style={{ background: '#1e293b', borderRadius: 12, padding: 28, border: '1px solid #334155', maxWidth: 640, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <CheckCircle size={32} color="#22c55e" />
          </div>
          <h3 style={{ color: 'white', fontSize: 20, fontWeight: 700, margin: '0 0 8px' }}>Report Submitted Successfully!</h3>
          <p style={{ color: '#94a3b8', fontSize: 14, margin: 0 }}>Your trackable maintenance issue report has been registered in the system.</p>
        </div>

        <div style={{ background: '#0f172a', borderRadius: 10, padding: 20, border: '1px solid #334155', marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 12, marginBottom: 12, borderBottom: '1px solid #1e293b' }}>
            <span style={{ color: '#94a3b8', fontSize: 13 }}>Report Tracking ID</span>
            <span style={{ color: '#22c55e', fontSize: 18, fontWeight: 700 }}>#{confirmedReport.id}</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13, marginBottom: 16 }}>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: 11, marginBottom: 2 }}>Status</span>
              <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: 'rgba(59,130,246,0.15)', color: '#3b82f6', display: 'inline-block' }}>
                {confirmedReport.status || 'Reported'}
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: 11, marginBottom: 2 }}>Timestamp</span>
              <span style={{ color: 'white', fontWeight: 500 }}>{new Date(confirmedReport.created_at).toLocaleString()}</span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: 11, marginBottom: 2 }}>Location</span>
              <span style={{ color: 'white', fontWeight: 500 }}>{confirmedReport.location}</span>
            </div>
            <div>
              <span style={{ color: '#64748b', display: 'block', fontSize: 11, marginBottom: 2 }}>Building</span>
              <span style={{ color: 'white', fontWeight: 500 }}>{confirmedReport.building || 'N/A'}</span>
            </div>
          </div>

          {photoPreview && (
            <div style={{ marginTop: 12 }}>
              <span style={{ color: '#64748b', display: 'block', fontSize: 11, marginBottom: 6 }}>Attached Photo</span>
              <img src={photoPreview} alt="Issue photo" style={{ width: '100%', maxHeight: 180, objectFit: 'cover', borderRadius: 8, border: '1px solid #334155' }} />
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={resetForm}
            style={{ flex: 1, padding: '10px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
          >
            Submit Another Report
          </button>
          {onCancel && (
            <button
              onClick={onCancel}
              style={{ flex: 1, padding: '10px 16px', background: 'linear-gradient(135deg, #22c55e, #16a34a)', border: 'none', borderRadius: 8, color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
            >
              Done / View Reports
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, border: '1px solid #334155', marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(34,197,94,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={18} color="#22c55e" />
          </div>
          <div>
            <h3 style={{ color: 'white', fontSize: 16, fontWeight: 600, margin: 0 }}>Campus Maintenance & Cleanliness Reporting</h3>
            <p style={{ color: '#94a3b8', fontSize: 12, margin: 0 }}>SCRUM05-F001 Issue Submission</p>
          </div>
        </div>
        {onCancel && (
          <button onClick={onCancel} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 4 }}>
            <X size={20} />
          </button>
        )}
      </div>

      {errorMessage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, marginBottom: 18 }}>
          <AlertCircle size={18} color="#ef4444" style={{ flexShrink: 0 }} />
          <span style={{ color: '#fca5a5', fontSize: 13 }}>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          {/* Location Dropdown Selection */}
          <div>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>
              Issue Location * <span style={{ color: '#ef4444' }}>(Required)</span>
            </label>
            <select
              value={formData.location}
              onChange={handleLocationChange}
              style={{ width: '100%', padding: '10px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: formData.location ? 'white' : '#64748b', fontSize: 13, outline: 'none', boxSizing: 'border-box' }}
            >
              <option value="">-- Select Campus Location --</option>
              {locations.map((loc) => (
                <option key={loc.id || loc.name} value={loc.name} style={{ background: '#0f172a', color: 'white' }}>
                  {loc.name} ({loc.building})
                </option>
              ))}
            </select>
          </div>

          {/* Photo File Input */}
          <div>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>
              Issue Photo * <span style={{ color: '#ef4444' }}>(Required)</span>
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handlePhotoChange}
              style={{ width: '100%', padding: '8px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#94a3b8', fontSize: 12, boxSizing: 'border-box' }}
            />
          </div>

          {/* Building */}
          <div>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Building / Block (Optional)</label>
            <input
              type="text"
              value={formData.building}
              onChange={(e) => setFormData({ ...formData, building: e.target.value })}
              placeholder="e.g. Block A"
              style={{ width: '100%', padding: '10px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, boxSizing: 'border-box' }}
            />
          </div>

          {/* Floor & Area */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Floor</label>
              <input
                type="text"
                value={formData.floor}
                onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                placeholder="e.g. 1st Floor"
                style={{ width: '100%', padding: '10px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Area</label>
              <input
                type="text"
                value={formData.area}
                onChange={(e) => setFormData({ ...formData, area: e.target.value })}
                placeholder="e.g. Washroom"
                style={{ width: '100%', padding: '10px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, boxSizing: 'border-box' }}
              />
            </div>
          </div>

          {/* Description */}
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, display: 'block', marginBottom: 6 }}>Description / Notes (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Provide specific details regarding the cleanliness or maintenance issue..."
              rows={3}
              style={{ width: '100%', padding: '10px 12px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: 'white', fontSize: 13, resize: 'vertical', boxSizing: 'border-box' }}
            />
          </div>
        </div>

        {/* Photo Preview */}
        {photoPreview && (
          <div style={{ marginBottom: 16, padding: 12, background: '#0f172a', borderRadius: 8, border: '1px solid #334155', display: 'flex', alignItems: 'center', gap: 14 }}>
            <img src={photoPreview} alt="Selected preview" style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 6 }} />
            <div>
              <span style={{ color: 'white', fontSize: 13, fontWeight: 500, display: 'block' }}>{formData.photo.name}</span>
              <span style={{ color: '#64748b', fontSize: 11 }}>{(formData.photo.size / 1024).toFixed(1)} KB</span>
            </div>
          </div>
        )}

        {/* Submit & Cancel Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12 }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              style={{ padding: '10px 18px', background: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#94a3b8', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={submitting || !formData.photo || !formData.location}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 24px',
              background: submitting || !formData.photo || !formData.location ? '#334155' : 'linear-gradient(135deg, #22c55e, #16a34a)',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
              cursor: submitting || !formData.photo || !formData.location ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <Send size={15} />
            {submitting ? 'Submitting Report...' : 'Submit Report'}
          </button>
        </div>
      </form>
    </div>
  );
}

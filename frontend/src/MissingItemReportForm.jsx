import { useState } from 'react';
import { Upload, AlertCircle, CheckCircle, X, Send, Search } from 'lucide-react';
import { lostAndFoundAPI } from './api';

const ITEM_CATEGORIES = [
  'Electronics',
  'ID Card',
  'Wallet / Purse',
  'Keys',
  'Documents',
  'Clothing',
  'Books / Notes',
  'Accessories',
  'Other',
];

export default function MissingItemReportForm({ onCancel, onSuccess }) {
  const [formData, setFormData] = useState({
    item_category: '',
    item_name: '',
    description: '',
    location: '',
    date_lost_or_found: '',
    identifying_details: '',
    hostel_type: '',
    image: null,
  });

  const [imagePreview, setImagePreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [errorMessage, setErrorMessage] = useState('');
  const [confirmedReport, setConfirmedReport] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    setErrors((prev) => ({
      ...prev,
      [name]: '',
    }));

    setErrorMessage('');
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (file) {
      setFormData((prev) => ({
        ...prev,
        image: file,
      }));

      setImagePreview(URL.createObjectURL(file));

      setErrors((prev) => ({
        ...prev,
        image: '',
      }));

      setErrorMessage('');
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.item_category) {
      newErrors.item_category = 'Please select an item category.';
    }

    if (!formData.item_name.trim()) {
      newErrors.item_name = 'Please enter the item name.';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Please enter item details.';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Please enter the location where the item was lost.';
    }

    if (!formData.date_lost_or_found) {
      newErrors.date_lost_or_found = 'Please select the date.';
    }

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    const payload = new FormData();

    payload.append('report_type', 'Missing');
    payload.append('item_category', formData.item_category);
    payload.append('item_name', formData.item_name.trim());
    payload.append('description', formData.description.trim());
    payload.append('location', formData.location.trim());
    payload.append('date_lost_or_found', formData.date_lost_or_found);

    if (formData.identifying_details.trim()) {
      payload.append(
        'identifying_details',
        formData.identifying_details.trim()
      );
    }

    if (formData.hostel_type) {
      payload.append('hostel_type', formData.hostel_type);
    }

    if (formData.image) {
      payload.append('image', formData.image);
    }

    try {
      const res = await lostAndFoundAPI.create(payload);

      setConfirmedReport(res.data);

      if (onSuccess) {
        onSuccess(res.data);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;

      if (typeof detail === 'string') {
        setErrorMessage(detail);
      } else {
        setErrorMessage(
          'Failed to submit missing item report. Please check the entered details.'
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setConfirmedReport(null);

    setFormData({
      item_category: '',
      item_name: '',
      description: '',
      location: '',
      date_lost_or_found: '',
      identifying_details: '',
      hostel_type: '',
      image: null,
    });

    setImagePreview(null);
    setErrors({});
    setErrorMessage('');
  };

  if (confirmedReport) {
    return (
      <div
        className="glass-card"
        style={{
          maxWidth: 640,
          margin: '0 auto 28px',
          padding: 36,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
          }}
        >
          <CheckCircle size={36} color="#059669" />
        </div>

        <h3
          style={{
            color: 'var(--text-main)',
            fontSize: 22,
            fontWeight: 800,
            margin: '0 0 8px',
          }}
        >
          Missing Item Report Submitted!
        </h3>

        <p
          style={{
            color: 'var(--text-muted)',
            fontSize: 14,
            margin: '0 0 24px',
          }}
        >
          Your missing item has been registered successfully.
        </p>

        <div
          style={{
            background: '#f8fafc',
            borderRadius: 16,
            padding: 24,
            border: '1px solid #e2e8f0',
            marginBottom: 28,
            textAlign: 'left',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingBottom: 14,
              marginBottom: 14,
              borderBottom: '1px solid #e2e8f0',
            }}
          >
            <span
              style={{
                color: 'var(--text-subtle)',
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Item Report ID
            </span>

            <span
              style={{
                color: '#059669',
                fontSize: 20,
                fontWeight: 800,
              }}
            >
              #{confirmedReport.item_report_id}
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 14,
              fontSize: 13,
            }}
          >
            <div>
              <span
                style={{
                  color: 'var(--text-subtle)',
                  display: 'block',
                  fontSize: 11,
                  marginBottom: 4,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                Item
              </span>

              <span
                style={{
                  color: 'var(--text-main)',
                  fontWeight: 600,
                }}
              >
                {confirmedReport.item_name}
              </span>
            </div>

            <div>
              <span
                style={{
                  color: 'var(--text-subtle)',
                  display: 'block',
                  fontSize: 11,
                  marginBottom: 4,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                Category
              </span>

              <span
                style={{
                  color: 'var(--text-main)',
                  fontWeight: 600,
                }}
              >
                {confirmedReport.item_category}
              </span>
            </div>

            <div>
              <span
                style={{
                  color: 'var(--text-subtle)',
                  display: 'block',
                  fontSize: 11,
                  marginBottom: 4,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                Status
              </span>

              <span className="badge badge-emerald">
                {confirmedReport.status || 'Submitted'}
              </span>
            </div>

            <div>
              <span
                style={{
                  color: 'var(--text-subtle)',
                  display: 'block',
                  fontSize: 11,
                  marginBottom: 4,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                Location
              </span>

              <span
                style={{
                  color: 'var(--text-main)',
                  fontWeight: 600,
                }}
              >
                {confirmedReport.location}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 14 }}>
          <button
            onClick={resetForm}
            className="btn btn-outline"
            style={{ flex: 1, padding: '12px 0' }}
          >
            Report Another Item
          </button>

          <button
            onClick={onCancel}
            className="btn btn-primary"
            style={{ flex: 1, padding: '12px 0' }}
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="glass-card"
      style={{
        marginBottom: 28,
        padding: 32,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 14,
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Search size={22} color="#059669" />
          </div>

          <div>
            <h3
              style={{
                color: 'var(--text-main)',
                fontSize: 18,
                fontWeight: 800,
                margin: 0,
              }}
            >
              Report Missing Item
            </h3>

            <p
              style={{
                color: 'var(--text-muted)',
                fontSize: 12,
                margin: '2px 0 0',
                fontWeight: 500,
              }}
            >
              Enter the item details and upload a photo to help locate it.
            </p>
          </div>
        </div>

        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              background: '#f1f5f9',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              padding: 8,
              borderRadius: 10,
            }}
          >
            <X size={18} />
          </button>
        )}
      </div>

      {errorMessage && (
        <div className="alert-banner alert-banner-error">
          <AlertCircle
            size={18}
            color="#dc2626"
            style={{ flexShrink: 0 }}
          />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 20,
            marginBottom: 20,
          }}
        >
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Item Category <span style={{ color: '#dc2626' }}>*</span>
            </label>

            <select
              name="item_category"
              value={formData.item_category}
              onChange={handleChange}
              className="form-select"
            >
              <option value="">-- Select Category --</option>

              {ITEM_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>

            {errors.item_category && (
              <small style={{ color: '#dc2626' }}>
                {errors.item_category}
              </small>
            )}
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Item Name <span style={{ color: '#dc2626' }}>*</span>
            </label>

            <input
              type="text"
              name="item_name"
              value={formData.item_name}
              onChange={handleChange}
              className="form-input"
              placeholder="Example: Black wallet"
            />

            {errors.item_name && (
              <small style={{ color: '#dc2626' }}>
                {errors.item_name}
              </small>
            )}
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Location Lost <span style={{ color: '#dc2626' }}>*</span>
            </label>

            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="form-input"
              placeholder="Example: Girls Hostel Block F"
            />

            {errors.location && (
              <small style={{ color: '#dc2626' }}>
                {errors.location}
              </small>
            )}
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Date Lost <span style={{ color: '#dc2626' }}>*</span>
            </label>

            <input
              type="date"
              name="date_lost_or_found"
              value={formData.date_lost_or_found}
              onChange={handleChange}
              className="form-input"
            />

            {errors.date_lost_or_found && (
              <small style={{ color: '#dc2626' }}>
                {errors.date_lost_or_found}
              </small>
            )}
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Hostel Type</label>

            <select
              name="hostel_type"
              value={formData.hostel_type}
              onChange={handleChange}
              className="form-select"
            >
              <option value="">-- Select Hostel --</option>
              <option value="Boys Hostel">Boys Hostel</option>
              <option value="Girls Hostel">Girls Hostel</option>
              <option value="NRI Hostel">NRI Hostel</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Item Photo
            </label>

            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="form-input"
              style={{ padding: '9px 14px' }}
            />
          </div>

          <div
            style={{ gridColumn: '1 / -1' }}
            className="form-group"
          >
            <label className="form-label">
              Item Description / Details{' '}
              <span style={{ color: '#dc2626' }}>*</span>
            </label>

            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the item and what happened..."
              rows={3}
              className="form-textarea"
            />

            {errors.description && (
              <small style={{ color: '#dc2626' }}>
                {errors.description}
              </small>
            )}
          </div>

          <div
            style={{ gridColumn: '1 / -1' }}
            className="form-group"
          >
            <label className="form-label">
              Identifying Details
            </label>

            <textarea
              name="identifying_details"
              value={formData.identifying_details}
              onChange={handleChange}
              placeholder="Colour, brand, serial number, marks, stickers, etc."
              rows={2}
              className="form-textarea"
            />
          </div>
        </div>

        {imagePreview && (
          <div
            style={{
              marginBottom: 20,
              padding: 14,
              background: '#f8fafc',
              borderRadius: 14,
              border: '1px solid #e2e8f0',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <img
              src={imagePreview}
              alt="Selected item"
              style={{
                width: 64,
                height: 64,
                objectFit: 'cover',
                borderRadius: 10,
                border: '1px solid #cbd5e1',
              }}
            />

            <div>
              <span
                style={{
                  color: 'var(--text-main)',
                  fontSize: 13,
                  fontWeight: 700,
                  display: 'block',
                }}
              >
                {formData.image.name}
              </span>

              <span
                style={{
                  color: 'var(--text-subtle)',
                  fontSize: 11,
                  fontWeight: 500,
                }}
              >
                {(formData.image.size / 1024).toFixed(1)} KB
              </span>
            </div>
          </div>
        )}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 12,
          }}
        >
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn btn-outline"
            >
              Cancel
            </button>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="btn btn-primary"
            style={{ padding: '12px 28px' }}
          >
            <Send size={16} />
            {submitting ? 'Submitting...' : 'Submit Missing Item'}
          </button>
        </div>
      </form>
    </div>
  );
}
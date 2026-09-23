import { useState } from 'react';
import { Search, CheckCircle, AlertCircle, Ticket, Coins, MapPin, User, RefreshCw } from 'lucide-react';
import { rewardsAPI } from './api';

const CATEGORY_STYLES = {
  Canteen: { hex: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
  Laundry: { hex: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
  'Hostel Stores': { hex: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
};

/**
 * HOSTELCARE-F003-UI-003 – Staff redemption voucher verification & fulfilment.
 * AC1 show reward + category on valid reference, AC2 block re-use of fulfilled voucher,
 * AC3 confirm -> status Fulfilled, AC4 show the fulfilment team for the category.
 */
export default function RedemptionVerification() {
  const [reference, setReference] = useState('');
  const [voucher, setVoucher] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const reset = () => {
    setReference('');
    setVoucher(null);
    setError('');
    setSuccess('');
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setVoucher(null);
    const ref = reference.trim().toUpperCase();
    if (!ref) {
      setError('Please enter a redemption reference.');
      return;
    }
    setLoading(true);
    try {
      const res = await rewardsAPI.lookupRedemption(ref);
      setVoucher(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to verify this voucher.');
    } finally {
      setLoading(false);
    }
  };

  const handleFulfill = async () => {
    if (!voucher) return;
    setError('');
    setLoading(true);
    try {
      const res = await rewardsAPI.fulfillRedemption(voucher.voucher_reference);
      setSuccess(res.data.message || 'Redemption fulfilled successfully');
      setVoucher({ ...voucher, fulfillment_status: 'Fulfilled', fulfilled_at: res.data.fulfilled_at });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to fulfill this voucher.');
    } finally {
      setLoading(false);
    }
  };

  const fulfilled = voucher?.fulfillment_status === 'Fulfilled';
  const cat = CATEGORY_STYLES[voucher?.reward_category] || { hex: '#64748b', bg: '#f8fafc', border: '#e2e8f0' };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ color: 'var(--text-main)', fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
          Redemption Verification
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, fontWeight: 500 }}>
          Verify a resident's voucher and hand over the reward (Canteen, Laundry, Hostel Stores)
        </p>
      </div>

      <div className="glass-card" style={{ maxWidth: 560, padding: 28, marginBottom: 24 }}>
        <form onSubmit={handleVerify}>
          <label className="form-label">Redemption Reference</label>
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              id="redemption-reference-input"
              type="text"
              className="form-input"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="e.g. A1B2C3D4-E5F6"
              style={{ flex: 1, fontFamily: 'monospace', textTransform: 'uppercase' }}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !reference.trim()} style={{ gap: 8 }}>
              <Search size={16} /> {loading && !voucher ? 'Checking...' : 'Verify'}
            </button>
          </div>
        </form>

        {error && (
          <div className="alert-banner alert-banner-error" style={{ marginTop: 16 }}>
            <AlertCircle size={16} color="var(--accent-red)" style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="alert-banner" style={{ marginTop: 16, display: 'flex', gap: 8, alignItems: 'center', color: '#059669', fontWeight: 600, fontSize: 13 }}>
            <CheckCircle size={16} /> <span>{success}</span>
          </div>
        )}
      </div>

      {voucher && (
        <div className="glass-card" style={{ maxWidth: 560, padding: 28 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', background: cat.bg, color: cat.hex, border: `1px solid ${cat.border}` }}>
              {voucher.reward_category}
            </span>
            <span style={{
              padding: '4px 12px', borderRadius: 999, fontSize: 12, fontWeight: 700,
              background: fulfilled ? '#ecfdf5' : '#fffbeb',
              color: fulfilled ? '#059669' : '#d97706',
              border: `1px solid ${fulfilled ? '#a7f3d0' : '#fde68a'}`,
            }}>
              {voucher.fulfillment_status}
            </span>
          </div>

          <h3 style={{ margin: '0 0 14px', fontSize: 20, fontWeight: 800, color: 'var(--text-main)' }}>{voucher.reward_name}</h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, color: 'var(--text-muted)', marginBottom: 22 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><Ticket size={15} /> <span style={{ fontFamily: 'monospace' }}>{voucher.voucher_reference}</span></div>
            {voucher.resident_name && <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><User size={15} /> {voucher.resident_name}</div>}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><Coins size={15} /> {voucher.tokens_deducted} tokens</div>
            {voucher.fulfillment_team && <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}><MapPin size={15} /> Fulfilment team: <b>{voucher.fulfillment_team}</b></div>}
            {fulfilled && voucher.fulfilled_at && <div>Fulfilled on {new Date(voucher.fulfilled_at).toLocaleString()}</div>}
          </div>

          {fulfilled ? (
            <div className="alert-banner alert-banner-error" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <AlertCircle size={16} color="var(--accent-red)" />
              <span>This voucher has already been fulfilled and cannot be used again.</span>
            </div>
          ) : (
            <button id="confirm-fulfill-btn" className="btn btn-primary" onClick={handleFulfill} disabled={loading} style={{ width: '100%', padding: '12px 0', gap: 8 }}>
              <CheckCircle size={16} /> {loading ? 'Confirming...' : 'Confirm & Mark as Fulfilled'}
            </button>
          )}

          <button className="btn btn-outline" onClick={reset} style={{ width: '100%', marginTop: 10, gap: 8 }}>
            <RefreshCw size={14} /> Verify another voucher
          </button>
        </div>
      )}
    </div>
  );
}

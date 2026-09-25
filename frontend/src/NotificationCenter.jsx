import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  CheckCircle2,
  AlertCircle,
  Clock,
  Coins,
  Ticket,
  Package,
  FileText,
  Check,
  CheckCheck,
  X,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { notificationsAPI } from './api';

export default function NotificationCenter({ onNavigate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filter, setFilter] = useState('all'); // 'all' | 'unread'
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationsAPI.getUnreadCount();
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch unread notification count', err);
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationsAPI.list({
        unread_only: filter === 'unread',
        limit: 50,
      });
      setNotifications(res.data.items);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch notifications', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    // Poll unread count every 20 seconds
    const interval = setInterval(fetchUnreadCount, 20000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, filter]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleMarkRead = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await notificationsAPI.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to mark read', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read', err);
    }
  };

  const handleNotificationClick = (item) => {
    if (!item.is_read) {
      handleMarkRead(item.id);
    }
    if (onNavigate) {
      if (item.reference_type === 'complaint') {
        onNavigate('reports');
      } else if (item.reference_type === 'token' || item.reference_type === 'redemption') {
        onNavigate('tokens');
      } else if (item.reference_type === 'claim' || item.reference_type === 'lost_and_found') {
        onNavigate('lost-and-found');
      }
      setIsOpen(false);
    }
  };

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'token_awarded':
        return <div style={{ background: '#ecfdf5', color: '#059669', padding: 8, borderRadius: 10, display: 'flex' }}><Coins size={18} /></div>;
      case 'complaint_verified':
      case 'claim_approved':
        return <div style={{ background: '#ecfdf5', color: '#059669', padding: 8, borderRadius: 10, display: 'flex' }}><CheckCircle2 size={18} /></div>;
      case 'complaint_rejected':
      case 'claim_rejected':
        return <div style={{ background: '#fef2f2', color: '#dc2626', padding: 8, borderRadius: 10, display: 'flex' }}><AlertCircle size={18} /></div>;
      case 'complaint_in_progress':
      case 'complaint_assigned':
        return <div style={{ background: '#fffbeb', color: '#d97706', padding: 8, borderRadius: 10, display: 'flex' }}><Clock size={18} /></div>;
      case 'redemption_created':
      case 'redemption_fulfilled':
        return <div style={{ background: '#f5f3ff', color: '#7c3aed', padding: 8, borderRadius: 10, display: 'flex' }}><Ticket size={18} /></div>;
      case 'item_returned':
      case 'claim_submitted':
      case 'claim_status_updated':
        return <div style={{ background: '#eff6ff', color: '#2563eb', padding: 8, borderRadius: 10, display: 'flex' }}><Package size={18} /></div>;
      default:
        return <div style={{ background: '#f1f5f9', color: '#475569', padding: 8, borderRadius: 10, display: 'flex' }}><FileText size={18} /></div>;
    }
  };

  const formatTimeAgo = (dateStr) => {
    try {
      const d = new Date(dateStr);
      const diffMs = Date.now() - d.getTime();
      const mins = Math.floor(diffMs / (1000 * 60));
      if (mins < 1) return 'Just now';
      if (mins < 60) return `${mins}m ago`;
      const hours = Math.floor(mins / 60);
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      if (days < 7) return `${days}d ago`;
      return d.toLocaleDateString();
    } catch {
      return '';
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        id="notification-bell-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notifications"
        style={{
          position: 'relative',
          width: 42,
          height: 42,
          borderRadius: 12,
          background: isOpen ? '#ecfdf5' : '#ffffff',
          border: isOpen ? '1px solid #a7f3d0' : '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
          transition: 'all 0.2s ease',
          color: isOpen ? '#059669' : '#475569',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = '#10b981';
          e.currentTarget.style.color = '#059669';
        }}
        onMouseLeave={(e) => {
          if (!isOpen) {
            e.currentTarget.style.borderColor = '#e2e8f0';
            e.currentTarget.style.color = '#475569';
          }
        }}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              minWidth: 19,
              height: 19,
              borderRadius: 10,
              background: '#dc2626',
              color: '#ffffff',
              fontSize: 10,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
              border: '2px solid #ffffff',
              boxShadow: '0 2px 6px rgba(220, 38, 38, 0.4)',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 52,
            right: 0,
            width: 380,
            maxHeight: 520,
            background: '#ffffff',
            borderRadius: 20,
            border: '1px solid #e2e8f0',
            boxShadow: '0 20px 40px -10px rgba(15, 23, 42, 0.16), 0 0 1px 1px rgba(15, 23, 42, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 100,
            overflow: 'hidden',
            animation: 'fadeIn 0.15s ease-out',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid #f1f5f9',
              background: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-main)' }}>Notifications</span>
                {unreadCount > 0 && (
                  <span style={{ background: '#ecfdf5', color: '#059669', fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 12, border: '1px solid #a7f3d0' }}>
                    {unreadCount} new
                  </span>
                )}
              </div>
              <p style={{ color: 'var(--text-subtle)', fontSize: 12, margin: '2px 0 0', fontWeight: 500 }}>
                Live updates for complaints, rewards &amp; claims
              </p>
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#059669',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '4px 8px',
                  borderRadius: 6,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#ecfdf5')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                title="Mark all as read"
              >
                <CheckCheck size={14} /> Read all
              </button>
            )}
          </div>

          {/* Filter tabs */}
          <div style={{ display: 'flex', padding: '8px 16px', background: '#f8fafc', borderBottom: '1px solid #f1f5f9', gap: 8 }}>
            <button
              onClick={() => setFilter('all')}
              style={{
                flex: 1,
                padding: '6px 0',
                borderRadius: 8,
                border: 'none',
                background: filter === 'all' ? '#ffffff' : 'transparent',
                color: filter === 'all' ? '#059669' : '#64748b',
                fontWeight: filter === 'all' ? 700 : 500,
                fontSize: 12,
                cursor: 'pointer',
                boxShadow: filter === 'all' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              }}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              style={{
                flex: 1,
                padding: '6px 0',
                borderRadius: 8,
                border: 'none',
                background: filter === 'unread' ? '#ffffff' : 'transparent',
                color: filter === 'unread' ? '#059669' : '#64748b',
                fontWeight: filter === 'unread' ? 700 : 500,
                fontSize: 12,
                cursor: 'pointer',
                boxShadow: filter === 'unread' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              }}
            >
              Unread ({unreadCount})
            </button>
          </div>

          {/* Notification List */}
          <div style={{ overflowY: 'auto', flex: 1, maxHeight: 380 }}>
            {loading ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Loading updates...
              </div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: 48, textAlign: 'center', color: '#94a3b8' }}>
                <Sparkles size={36} color="#cbd5e1" style={{ margin: '0 auto 10px', display: 'block' }} />
                <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: 14 }}>All caught up!</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  {filter === 'unread' ? 'No unread notifications' : 'No notification history yet'}
                </div>
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleNotificationClick(item)}
                  style={{
                    padding: '14px 18px',
                    display: 'flex',
                    gap: 12,
                    borderBottom: '1px solid #f8fafc',
                    background: item.is_read ? '#ffffff' : '#f0fdf4',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = item.is_read ? '#f8fafc' : '#dcfce7';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = item.is_read ? '#ffffff' : '#f0fdf4';
                  }}
                >
                  <div style={{ flexShrink: 0, marginTop: 2 }}>
                    {getEventIcon(item.event_type)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 6 }}>
                      <span
                        style={{
                          fontSize: 13,
                          fontWeight: item.is_read ? 600 : 800,
                          color: 'var(--text-main)',
                          lineHeight: 1.3,
                        }}
                      >
                        {item.title}
                      </span>
                      <span style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap', flexShrink: 0 }}>
                        {formatTimeAgo(item.created_at)}
                      </span>
                    </div>
                    <p
                      style={{
                        margin: '4px 0 0',
                        fontSize: 12,
                        color: item.is_read ? '#64748b' : '#334155',
                        lineHeight: 1.45,
                        fontWeight: item.is_read ? 400 : 500,
                      }}
                    >
                      {item.message}
                    </p>
                  </div>
                  {!item.is_read && (
                    <div
                      style={{
                        position: 'absolute',
                        right: 12,
                        bottom: 12,
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: '#059669',
                      }}
                    />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

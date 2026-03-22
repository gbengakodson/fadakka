import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import './Settings.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const Settings = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('password');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // 2FA state
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [twoFactorSecret, setTwoFactorSecret] = useState('');

  // Notification preferences
  const [notifications, setNotifications] = useState({
    email_deposits: true,
    email_withdrawals: true,
    email_price_alerts: true,
    email_auto_sell: true,
    push_notifications: false
  });

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(
        `${API_URL}/auth/change-password/`,
        {
          current_password: passwordData.current_password,
          new_password: passwordData.new_password
        },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to change password' });
    } finally {
      setLoading(false);
    }
  };

  const handleTwoFactorSetup = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/auth/2fa/setup/`,
        {},
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      setTwoFactorSecret(response.data.secret);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to setup 2FA' });
    }
  };

  const handleTwoFactorEnable = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/auth/2fa/enable/`,
        { code: twoFactorCode },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      setTwoFactorEnabled(true);
      setMessage({ type: 'success', text: '2FA enabled successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Invalid verification code' });
    }
  };

  const handleNotificationChange = (e) => {
    setNotifications({
      ...notifications,
      [e.target.name]: e.target.checked
    });
  };

  const handleNotificationSave = async () => {
    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/auth/notification-preferences/`,
        notifications,
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      setMessage({ type: 'success', text: 'Notification preferences saved!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save preferences' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      try {
        await axios.delete(
          `${API_URL}/auth/account/`,
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        );
        logout();
        window.location.href = '/';
      } catch (error) {
        setMessage({ type: 'error', text: 'Failed to delete account' });
      }
    }
  };

  return (
    <div className="settings-container">
      <h1>Settings</h1>

      {message.text && (
        <div className={`settings-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="settings-tabs">
        <button
          className={`tab-btn ${activeTab === 'password' ? 'active' : ''}`}
          onClick={() => setActiveTab('password')}
        >
          🔒 Security
        </button>
        <button
          className={`tab-btn ${activeTab === '2fa' ? 'active' : ''}`}
          onClick={() => setActiveTab('2fa')}
        >
          📱 Two-Factor Auth
        </button>
        <button
          className={`tab-btn ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          🔔 Notifications
        </button>
        <button
          className={`tab-btn ${activeTab === 'account' ? 'active' : ''}`}
          onClick={() => setActiveTab('account')}
        >
          ⚠️ Account
        </button>
      </div>

      <div className="settings-content">
        {/* Password Change Tab */}
        {activeTab === 'password' && (
          <div className="settings-card">
            <h2>Change Password</h2>
            <form onSubmit={handlePasswordSubmit}>
              <div className="form-group">
                <label>Current Password</label>
                <input
                  type="password"
                  name="current_password"
                  value={passwordData.current_password}
                  onChange={handlePasswordChange}
                  required
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  name="new_password"
                  value={passwordData.new_password}
                  onChange={handlePasswordChange}
                  required
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  name="confirm_password"
                  value={passwordData.confirm_password}
                  onChange={handlePasswordChange}
                  required
                  className="form-input"
                />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Updating...' : 'Update Password'}
              </button>
            </form>

            <div className="security-tips">
              <h3>Password Tips</h3>
              <ul>
                <li>Use at least 12 characters</li>
                <li>Include uppercase and lowercase letters</li>
                <li>Add numbers and special characters</li>
                <li>Don't reuse passwords from other sites</li>
              </ul>
            </div>
          </div>
        )}

        {/* 2FA Tab */}
        {activeTab === '2fa' && (
          <div className="settings-card">
            <h2>Two-Factor Authentication</h2>
            <p className="description">
              Add an extra layer of security to your account by requiring a verification code
              when logging in.
            </p>

            {!twoFactorEnabled ? (
              <>
                {!twoFactorSecret ? (
                  <button className="btn-primary" onClick={handleTwoFactorSetup}>
                    Enable 2FA
                  </button>
                ) : (
                  <div className="twofa-setup">
                    <div className="qr-code">
                      <img
                        src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${twoFactorSecret}`}
                        alt="2FA QR Code"
                      />
                    </div>
                    <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
                    <div className="secret-key">
                      <span>Or enter this key manually:</span>
                      <code>{twoFactorSecret}</code>
                      <button onClick={() => navigator.clipboard.writeText(twoFactorSecret)}>
                        📋 Copy
                      </button>
                    </div>
                    <div className="form-group">
                      <label>Verification Code</label>
                      <input
                        type="text"
                        value={twoFactorCode}
                        onChange={(e) => setTwoFactorCode(e.target.value)}
                        placeholder="Enter 6-digit code"
                        className="form-input"
                      />
                    </div>
                    <button className="btn-primary" onClick={handleTwoFactorEnable}>
                      Verify and Enable
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="twofa-enabled">
                <p>✅ Two-factor authentication is <strong>enabled</strong></p>
                <button className="btn-secondary" onClick={() => setTwoFactorEnabled(false)}>
                  Disable 2FA
                </button>
              </div>
            )}
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="settings-card">
            <h2>Notification Preferences</h2>
            <div className="notification-settings">
              <div className="notification-group">
                <h3>Email Notifications</h3>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="email_deposits"
                    checked={notifications.email_deposits}
                    onChange={handleNotificationChange}
                  />
                  <span>Deposit confirmations</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="email_withdrawals"
                    checked={notifications.email_withdrawals}
                    onChange={handleNotificationChange}
                  />
                  <span>Withdrawal confirmations</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="email_price_alerts"
                    checked={notifications.email_price_alerts}
                    onChange={handleNotificationChange}
                  />
                  <span>Price alerts</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="email_auto_sell"
                    checked={notifications.email_auto_sell}
                    onChange={handleNotificationChange}
                  />
                  <span>Auto-sell notifications</span>
                </label>
              </div>

              <div className="notification-group">
                <h3>Push Notifications</h3>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="push_notifications"
                    checked={notifications.push_notifications}
                    onChange={handleNotificationChange}
                  />
                  <span>Enable push notifications</span>
                </label>
              </div>

              <button className="btn-primary" onClick={handleNotificationSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
          </div>
        )}

        {/* Account Tab */}
        {activeTab === 'account' && (
          <div className="settings-card danger">
            <h2>Danger Zone</h2>
            <div className="danger-section">
              <div className="danger-item">
                <div>
                  <strong>Delete Account</strong>
                  <p>Permanently delete your account and all associated data.</p>
                </div>
                <button className="btn-danger" onClick={handleDeleteAccount}>
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;
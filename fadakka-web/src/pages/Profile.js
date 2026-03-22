import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import './Profile.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const Profile = () => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    referral_code: '',
    solana_address: '',
    is_verified: false,
    kyc_status: 'pending'
  });
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [formData, setFormData] = useState({});

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/auth/profile/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setProfile(response.data);
      setFormData(response.data);
    } catch (error) {
      console.error('Error fetching profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await axios.put(
        `${API_URL}/auth/profile/`,
        formData,
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      setProfile(response.data);
      setEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update profile' });
    } finally {
      setSaving(false);
    }
  };

  const copyReferralCode = () => {
    navigator.clipboard.writeText(profile.referral_code);
    setMessage({ type: 'success', text: 'Referral code copied!' });
    setTimeout(() => setMessage({ type: '', text: '' }), 2000);
  };

  const getKYCStatusBadge = () => {
    const status = profile.kyc_status || 'not_submitted';
    switch(status) {
      case 'verified':
        return <span className="kyc-badge verified">✅ Verified</span>;
      case 'pending':
        return <span className="kyc-badge pending">⏳ Pending</span>;
      case 'rejected':
        return <span className="kyc-badge rejected">❌ Rejected</span>;
      default:
        return <span className="kyc-badge not-submitted">📝 Not Submitted</span>;
    }
  };

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="spinner"></div>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>My Profile</h1>
        {!editing && (
          <button className="edit-btn" onClick={() => setEditing(true)}>
            ✏️ Edit Profile
          </button>
        )}
      </div>

      {message.text && (
        <div className={`profile-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="profile-content">
        {/* Profile Card */}
        <div className="profile-card">
          <div className="profile-avatar">
            {profile.username?.charAt(0).toUpperCase()}
          </div>
          <div className="profile-info">
            {!editing ? (
              <>
                <h2>{profile.first_name} {profile.last_name}</h2>
                <p className="username">@{profile.username}</p>
                <p className="email">{profile.email}</p>
                <p className="phone">{profile.phone || 'No phone number added'}</p>
              </>
            ) : (
              <div className="edit-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>First Name</label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name || ''}
                      onChange={handleInputChange}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Last Name</label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name || ''}
                      onChange={handleInputChange}
                      className="form-input"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email || ''}
                    onChange={handleInputChange}
                    className="form-input"
                    disabled
                  />
                </div>
                <div className="form-group">
                  <label>Phone Number</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone || ''}
                    onChange={handleInputChange}
                    placeholder="+1 234 567 8900"
                    className="form-input"
                  />
                </div>
                <div className="edit-actions">
                  <button className="btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
                  <button className="btn-primary" onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Referral Info */}
        <div className="info-card">
          <h3>Referral Information</h3>
          <div className="referral-info">
            <div className="referral-code-box">
              <span className="label">Your Referral Code:</span>
              <div className="code-display">
                <code>{profile.referral_code}</code>
                <button className="copy-btn" onClick={copyReferralCode}>
                  📋 Copy
                </button>
              </div>
            </div>
            <div className="referral-link-box">
              <span className="label">Referral Link:</span>
              <div className="link-display">
                <code>{`${window.location.origin}/register?ref=${profile.referral_code}`}</code>
                <button
                  className="copy-btn"
                  onClick={() => navigator.clipboard.writeText(`${window.location.origin}/register?ref=${profile.referral_code}`)}
                >
                  📋 Copy
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Wallet Info */}
        <div className="info-card">
          <h3>Wallet Information</h3>
          <div className="wallet-info">
            <div className="wallet-row">
              <span className="label">Solana Address:</span>
              <div className="wallet-address">
                <code>{profile.solana_address || 'Not created yet'}</code>
                {profile.solana_address && (
                  <button
                    className="copy-btn"
                    onClick={() => navigator.clipboard.writeText(profile.solana_address)}
                  >
                    📋 Copy
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* KYC Status */}
        <div className="info-card">
          <h3>Verification Status</h3>
          <div className="kyc-info">
            <div className="kyc-status">
              <span className="label">KYC Status:</span>
              {getKYCStatusBadge()}
            </div>
            {profile.kyc_status !== 'verified' && (
              <button className="kyc-btn" onClick={() => window.location.href = '/dashboard?kyc=true'}>
                Complete KYC Verification
              </button>
            )}
          </div>
        </div>

        {/* Security Info */}
        <div className="info-card">
          <h3>Security</h3>
          <div className="security-info">
            <button className="security-btn" onClick={() => window.location.href = '/settings'}>
              Change Password
            </button>
            <button className="security-btn" onClick={() => window.location.href = '/settings'}>
              Enable 2FA
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
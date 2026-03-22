import React, { useState, useEffect } from 'react';
import axios from 'axios';
import KYCSumbitForm from './KYCSumbitForm';
import './KYCStatus.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const KYCStatus = () => {
  const [kycData, setKycData] = useState({
    status: 'not_submitted',
    submitted_at: null,
    verified_at: null,
    can_withdraw_large: false
  });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchKYCStatus();
  }, []);

  const fetchKYCStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/wallet/kyc/status/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setKycData(response.data);
    } catch (err) {
      console.error('Error fetching KYC status:', err);
      setError('Failed to load KYC status');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = () => {
    switch(kycData.status) {
      case 'verified':
        return <span className="kyc-badge verified">✅ Verified</span>;
      case 'pending':
        return <span className="kyc-badge pending">⏳ Pending Review</span>;
      case 'rejected':
        return <span className="kyc-badge rejected">❌ Rejected</span>;
      default:
        return <span className="kyc-badge not-submitted">📝 Not Submitted</span>;
    }
  };

  const getStatusMessage = () => {
    switch(kycData.status) {
      case 'verified':
        return "Your identity has been verified. You can now withdraw up to $50,000 per day.";
      case 'pending':
        return "Your documents are being reviewed. This usually takes 1-2 business days.";
      case 'rejected':
        return "Your verification was rejected. Please submit new documents.";
      default:
        return "Verify your identity to increase your withdrawal limit to $50,000 per day.";
    }
  };

  if (loading) {
    return (
      <div className="kyc-status-card loading">
        <div className="spinner-small"></div>
        <span>Loading KYC status...</span>
      </div>
    );
  }

  return (
    <>
      <div className="kyc-status-card">
        <div className="kyc-header">
          <div className="kyc-title">
            <span className="kyc-icon">🪪</span>
            <h3>Identity Verification (KYC)</h3>
          </div>
          {getStatusBadge()}
        </div>

        <p className="kyc-message">{getStatusMessage()}</p>

        <div className="kyc-limits">
          <div className="limit-item">
            <span className="limit-label">Current Daily Limit:</span>
            <span className="limit-value">
              ${kycData.status === 'verified' ? '50,000' : '1,000'} USDC
            </span>
          </div>
          {kycData.status === 'verified' && kycData.verified_at && (
            <div className="limit-item">
              <span className="limit-label">Verified on:</span>
              <span className="limit-value">
                {new Date(kycData.verified_at).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        {kycData.status === 'not_submitted' && (
          <button
            className="kyc-action-btn"
            onClick={() => setShowForm(true)}
          >
            Start Verification
          </button>
        )}

        {kycData.status === 'rejected' && (
          <button
            className="kyc-action-btn"
            onClick={() => setShowForm(true)}
          >
            Resubmit Documents
          </button>
        )}

        {kycData.status === 'pending' && (
          <div className="kyc-pending-note">
            <p>We'll notify you via email once your verification is complete.</p>
          </div>
        )}
      </div>

      {showForm && (
        <KYCSumbitForm
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false);
            fetchKYCStatus();
          }}
        />
      )}
    </>
  );
};

export default KYCStatus;
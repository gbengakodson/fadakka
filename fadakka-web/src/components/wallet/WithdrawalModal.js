import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './WalletModals.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const WithdrawalModal = ({ isOpen, onClose, onSuccess, maxAmount }) => {
  console.log('🟠 WithdrawalModal rendering, isOpen:', isOpen, 'maxAmount:', maxAmount);

  const [formData, setFormData] = useState({
    to_address: '',
    amount: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  const [kycCheck, setKycCheck] = useState(null);
  const [checkingLimit, setCheckingLimit] = useState(false);

  // Check withdrawal limit when amount changes
  useEffect(() => {
    const checkLimit = async () => {
      if (formData.amount && parseFloat(formData.amount) > 0) {
        setCheckingLimit(true);
        try {
          const response = await axios.post(
            `${API_URL}/wallet/kyc/check-withdraw/`,
            { amount: parseFloat(formData.amount) },
            { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
          );
          setKycCheck(response.data);

          if (!response.data.can_withdraw) {
            setError(`Daily limit exceeded. Remaining: $${response.data.remaining.toFixed(2)}`);
          } else {
            setError('');
          }
        } catch (err) {
          console.error('Error checking limit:', err);
        } finally {
          setCheckingLimit(false);
        }
      }
    };

    const timeoutId = setTimeout(checkLimit, 500);
    return () => clearTimeout(timeoutId);
  }, [formData.amount]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const validateForm = () => {
    if (!formData.to_address) {
      setError('Destination address is required');
      return false;
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('Amount must be greater than 0');
      return false;
    }
    if (parseFloat(formData.amount) > maxAmount) {
      setError(`Amount exceeds available balance of $${maxAmount.toFixed(2)}`);
      return false;
    }
    if (kycCheck && !kycCheck.can_withdraw) {
      setError(`Daily limit exceeded. Remaining: $${kycCheck.remaining.toFixed(2)}`);
      return false;
    }
    return true;
  };

  const handleNext = () => {
    setError('');
    if (validateForm()) {
      setStep(2);
    }
  };

  const handleBack = () => {
    setStep(1);
    setError('');
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_URL}/wallet/usdc/withdraw/`,
        formData,
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );

      if (response.data.success) {
        onSuccess(response.data);
        onClose();
        setFormData({ to_address: '', amount: '' });
        setStep(1);
      }
    } catch (err) {
      console.error('Withdrawal error:', err);
      const errorData = err.response?.data;

      if (errorData?.requires_kyc) {
        setError(
          <div>
            <p>❌ {errorData.error}</p>
            <p>Daily limit: ${errorData.daily_limit}</p>
            <p>Used today: ${errorData.used_today}</p>
            <p>Remaining: ${errorData.remaining}</p>
            <button
              className="kyc-prompt-btn"
              onClick={() => window.location.href = '/dashboard?kyc=true'}
            >
              Complete KYC Verification
            </button>
          </div>
        );
      } else {
        setError(errorData?.error || 'Withdrawal failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const calculateFee = (amount) => {
    const fee = parseFloat(amount || 0) * 0.001;
    return fee.toFixed(2);
  };

  const calculateNet = (amount) => {
    const net = parseFloat(amount || 0) - parseFloat(calculateFee(amount));
    return net.toFixed(2);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Withdraw USDC</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {error && <div className="error-message">{error}</div>}

          {kycCheck && !kycCheck.is_verified && parseFloat(formData.amount) > 1000 && (
            <div className="kyc-warning">
              <p>⚠️ Amount exceeds unverified limit ($1,000)</p>
              <p>Please complete KYC verification to withdraw larger amounts</p>
            </div>
          )}

          {step === 1 ? (
            <>
              <div className="info-box">
                <p>Available Balance: <strong>${maxAmount.toFixed(2)} USDC</strong></p>
                {kycCheck && (
                  <p className="limit-info">
                    Daily Limit Remaining: <strong>${kycCheck.remaining.toFixed(2)}</strong>
                    {!kycCheck.is_verified && <span className="unverified-badge">Unverified</span>}
                  </p>
                )}
              </div>

              <div className="form-group">
                <label>Destination Address (Solana)</label>
                <input
                  type="text"
                  name="to_address"
                  value={formData.to_address}
                  onChange={handleChange}
                  placeholder="Enter Solana wallet address"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Amount (USDC)</label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleChange}
                  placeholder="0.00"
                  min="1"
                  step="0.01"
                  className="form-input"
                />
                {checkingLimit && <span className="checking">Checking limit...</span>}
              </div>

              {formData.amount && (
                <div className="fee-breakdown">
                  <div className="fee-row">
                    <span>Amount:</span>
                    <span>${parseFloat(formData.amount || 0).toFixed(2)} USDC</span>
                  </div>
                  <div className="fee-row">
                    <span>Fee (0.1%):</span>
                    <span>- ${calculateFee(formData.amount)} USDC</span>
                  </div>
                  <div className="fee-row total">
                    <span>You'll receive:</span>
                    <span>${calculateNet(formData.amount)} USDC</span>
                  </div>
                </div>
              )}

              <div className="warning-box">
                ⚠️ Double-check the address! Transactions cannot be reversed.
              </div>
            </>
          ) : (
            <>
              <div className="confirm-box">
                <h3>Confirm Withdrawal</h3>

                <div className="confirm-row">
                  <span>To Address:</span>
                  <code>{formData.to_address}</code>
                </div>

                <div className="confirm-row">
                  <span>Amount:</span>
                  <strong>${parseFloat(formData.amount).toFixed(2)} USDC</strong>
                </div>

                <div className="confirm-row">
                  <span>Fee (0.1%):</span>
                  <span>- ${calculateFee(formData.amount)} USDC</span>
                </div>

                <div className="confirm-row total">
                  <span>Net Amount:</span>
                  <strong>${calculateNet(formData.amount)} USDC</strong>
                </div>
              </div>

              <div className="warning-box">
                ⚠️ This action cannot be undone. Please verify all details.
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          {step === 1 ? (
            <>
              <button className="btn-secondary" onClick={onClose}>Cancel</button>
              <button
                className="btn-primary"
                onClick={handleNext}
                disabled={!formData.to_address || !formData.amount || checkingLimit}
              >
                Next
              </button>
            </>
          ) : (
            <>
              <button className="btn-secondary" onClick={handleBack}>Back</button>
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Confirm Withdrawal'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default WithdrawalModal;
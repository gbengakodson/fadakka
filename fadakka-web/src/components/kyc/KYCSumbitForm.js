import React, { useState } from 'react';
import axios from 'axios';
import './KYCStatus.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const KYCSumbitForm = ({ onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    nationality: '',
    id_number: '',
    id_type: 'passport',
    id_front: null,
    id_back: null,
    selfie: null,
    proof_of_address: null
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const { name, files } = e.target;
    if (files.length > 0) {
      setFormData(prev => ({ ...prev, [name]: files[0] }));
    }
  };

  const validateStep1 = () => {
    if (!formData.full_name) {
      setError('Full name is required');
      return false;
    }
    if (!formData.date_of_birth) {
      setError('Date of birth is required');
      return false;
    }
    if (!formData.nationality) {
      setError('Nationality is required');
      return false;
    }
    if (!formData.id_number) {
      setError('ID number is required');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.id_front) {
      setError('Front of ID is required');
      return false;
    }
    if (!formData.selfie) {
      setError('Selfie is required');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    setError('');
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      setStep(3);
    }
  };

  const handleBack = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    const submitData = new FormData();
    Object.keys(formData).forEach(key => {
      if (formData[key]) {
        submitData.append(key, formData[key]);
      }
    });

    try {
      const response = await axios.post(
        `${API_URL}/wallet/kyc/submit/`,
        submitData,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      if (response.data.success) {
        onSuccess();
      }
    } catch (err) {
      console.error('KYC submission error:', err);
      setError(err.response?.data?.error || 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="kyc-modal-overlay">
      <div className="kyc-modal-content">
        <div className="kyc-modal-header">
          <h2>Identity Verification</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="kyc-modal-body">
          {/* Progress Steps */}
          <div className="kyc-progress">
            <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>
              <span className="step-number">1</span>
              <span className="step-label">Personal Info</span>
            </div>
            <div className={`progress-line ${step >= 2 ? 'active' : ''}`}></div>
            <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
              <span className="step-number">2</span>
              <span className="step-label">Documents</span>
            </div>
            <div className={`progress-line ${step >= 3 ? 'active' : ''}`}></div>
            <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
              <span className="step-number">3</span>
              <span className="step-label">Review</span>
            </div>
          </div>

          {error && <div className="kyc-error">{error}</div>}

          {step === 1 && (
            <div className="kyc-step">
              <h3>Personal Information</h3>

              <div className="form-group">
                <label>Full Name (as on ID)</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="John Doe"
                  className="form-input"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Date of Birth</label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Nationality</label>
                  <select
                    name="nationality"
                    value={formData.nationality}
                    onChange={handleChange}
                    className="form-input"
                  >
                    <option value="">Select country</option>
                    <option value="US">United States</option>
                    <option value="UK">United Kingdom</option>
                    <option value="CA">Canada</option>
                    <option value="AU">Australia</option>
                    <option value="NG">Nigeria</option>
                    <option value="GH">Ghana</option>
                    <option value="KE">Kenya</option>
                    <option value="ZA">South Africa</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>ID Number</label>
                <input
                  type="text"
                  name="id_number"
                  value={formData.id_number}
                  onChange={handleChange}
                  placeholder="Passport / Driver's License / National ID number"
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>ID Type</label>
                <select
                  name="id_type"
                  value={formData.id_type}
                  onChange={handleChange}
                  className="form-input"
                >
                  <option value="passport">Passport</option>
                  <option value="drivers_license">Driver's License</option>
                  <option value="national_id">National ID</option>
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="kyc-step">
              <h3>Document Upload</h3>

              <div className="upload-section">
                <label className="upload-label">
                  <span>Front of ID *</span>
                  <input
                    type="file"
                    name="id_front"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  {formData.id_front && (
                    <span className="file-name">✓ {formData.id_front.name}</span>
                  )}
                </label>

                <label className="upload-label">
                  <span>Selfie with ID *</span>
                  <input
                    type="file"
                    name="selfie"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  {formData.selfie && (
                    <span className="file-name">✓ {formData.selfie.name}</span>
                  )}
                </label>

                <label className="upload-label">
                  <span>Back of ID (optional)</span>
                  <input
                    type="file"
                    name="id_back"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  {formData.id_back && (
                    <span className="file-name">✓ {formData.id_back.name}</span>
                  )}
                </label>

                <label className="upload-label">
                  <span>Proof of Address (optional)</span>
                  <input
                    type="file"
                    name="proof_of_address"
                    accept="image/*,.pdf"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  {formData.proof_of_address && (
                    <span className="file-name">✓ {formData.proof_of_address.name}</span>
                  )}
                </label>
              </div>

              <div className="upload-note">
                <p>📌 Please ensure all documents are clear and legible</p>
                <p>📌 Accepted formats: JPG, PNG, PDF (max 5MB each)</p>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="kyc-step">
              <h3>Review Information</h3>

              <div className="review-box">
                <h4>Personal Details</h4>
                <p><strong>Name:</strong> {formData.full_name}</p>
                <p><strong>Date of Birth:</strong> {formData.date_of_birth}</p>
                <p><strong>Nationality:</strong> {formData.nationality}</p>
                <p><strong>ID Type:</strong> {formData.id_type}</p>
                <p><strong>ID Number:</strong> {formData.id_number}</p>
              </div>

              <div className="review-box">
                <h4>Documents</h4>
                <p><strong>ID Front:</strong> {formData.id_front?.name || 'Not uploaded'}</p>
                <p><strong>Selfie:</strong> {formData.selfie?.name || 'Not uploaded'}</p>
                <p><strong>ID Back:</strong> {formData.id_back?.name || 'Not uploaded'}</p>
                <p><strong>Proof of Address:</strong> {formData.proof_of_address?.name || 'Not uploaded'}</p>
              </div>

              <div className="terms-checkbox">
                <input type="checkbox" id="terms" required />
                <label htmlFor="terms">
                  I confirm that all information provided is accurate and true
                </label>
              </div>
            </div>
          )}
        </div>

        <div className="kyc-modal-footer">
          {step > 1 && (
            <button className="btn-secondary" onClick={handleBack}>
              Back
            </button>
          )}
          {step < 3 ? (
            <button className="btn-primary" onClick={handleNext}>
              Next
            </button>
          ) : (
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? 'Submitting...' : 'Submit Verification'}
            </button>
          )}
          {step === 1 && (
            <button className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default KYCSumbitForm;
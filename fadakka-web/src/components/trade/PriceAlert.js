import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './PriceAlert.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const PriceAlert = ({ token, onClose }) => {
  const [alertType, setAlertType] = useState('above');
  const [targetPrice, setTargetPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(
        `${API_URL}/volatility/price-alerts/`,
        {
          token_id: token.id,
          alert_type: alertType,
          target_price: targetPrice
        },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      onClose(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="alert-modal-overlay">
      <div className="alert-modal">
        <h3>Set Price Alert for {token.symbol}</h3>
        <form onSubmit={handleSubmit}>
          <div className="alert-type">
            <label>
              <input
                type="radio"
                value="above"
                checked={alertType === 'above'}
                onChange={(e) => setAlertType(e.target.value)}
              />
              Alert when price goes above
            </label>
            <label>
              <input
                type="radio"
                value="below"
                checked={alertType === 'below'}
                onChange={(e) => setAlertType(e.target.value)}
              />
              Alert when price goes below
            </label>
          </div>

          <div className="alert-price">
            <input
              type="number"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              placeholder="Target price in USDC"
              step="0.01"
              required
            />
          </div>

          {error && <div className="alert-error">{error}</div>}

          <div className="alert-actions">
            <button type="button" onClick={() => onClose(false)}>Cancel</button>
            <button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Set Alert'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PriceAlert;
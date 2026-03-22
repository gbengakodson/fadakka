import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import './YieldDashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

function YieldDashboard() {
  const { user } = useAuth();
  const [distributions, setDistributions] = useState([]);
  const [yieldData, setYieldData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchYieldData();
  }, []);

  const fetchYieldData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log("🔵 Fetching yield data...");

      // Fetch yield distributions
      const distributionsResponse = await axios.get(`${API_URL}/volatility/yield-distributions/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      console.log("🔵 Distributions received:", distributionsResponse.data);
      setDistributions(distributionsResponse.data);

      // Fetch user tokens to calculate totals
      const tokensResponse = await axios.get(`${API_URL}/volatility/user-tokens/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      // Calculate totals
      let totalYieldEarned = 0;
      let currentPortfolioValue = 0;

      tokensResponse.data.forEach(holding => {
        totalYieldEarned += holding.yield_earned_total || 0;
        currentPortfolioValue += holding.current_value || 0;
      });

      // Get last distribution
      const lastDistribution = distributionsResponse.data[0];

      setYieldData({
        total_yield_earned: totalYieldEarned,
        current_value: currentPortfolioValue,
        projected_annual_yield: {
          min: currentPortfolioValue * 0.08,
          max: currentPortfolioValue * 0.10
        },
        last_distribution: lastDistribution ? {
          date: new Date(lastDistribution.date).toLocaleString(),
          amount: lastDistribution.amount,
          token: lastDistribution.token
        } : null,
        next_distribution_date: getNextDistributionDate()
      });

    } catch (error) {
      console.error('Error fetching yield data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getNextDistributionDate = () => {
    const today = new Date();
    const nextHour = new Date(today.getFullYear(), today.getMonth(), today.getDate(), today.getHours() + 1, 0, 0);
    return nextHour.toLocaleString();
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);
  };

  if (loading) {
    return (
      <div className="yield-loading">
        <div className="spinner"></div>
        <p>Loading yield data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="yield-error">
        <p>Error: {error}</p>
        <button onClick={fetchYieldData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="yield-dashboard">
      <h1>Yield Dashboard</h1>
      <p className="welcome-message">Welcome back, {user?.username}!</p>

      {/* Summary Cards */}
      <div className="yield-summary">
        <div className="summary-card">
          <h3>💰 Total Yield Earned</h3>
          <div className="value">{formatCurrency(yieldData?.total_yield_earned || 0)}</div>
        </div>

        <div className="summary-card">
          <h3>📊 Current Portfolio Value</h3>
          <div className="value">{formatCurrency(yieldData?.current_value || 0)}</div>
        </div>

        <div className="summary-card">
          <h3>🌱 Projected Annual Yield</h3>
          <div className="value-range">
            <span>{formatCurrency(yieldData?.projected_annual_yield?.min || 0)}</span>
            <span className="separator"> - </span>
            <span>{formatCurrency(yieldData?.projected_annual_yield?.max || 0)}</span>
          </div>
          <div className="sub-text">8-10% of portfolio value</div>
        </div>
      </div>

      {/* Last Distribution */}
      {yieldData?.last_distribution && (
        <div className="last-distribution">
          <h3>📅 Last Distribution</h3>
          <div className="distribution-details">
            <div className="detail-item">
              <span>Date:</span>
              <strong>{yieldData.last_distribution.date}</strong>
            </div>
            <div className="detail-item">
              <span>Token:</span>
              <strong>{yieldData.last_distribution.token}</strong>
            </div>
            <div className="detail-item">
              <span>Amount:</span>
              <strong className="profit">+{formatCurrency(yieldData.last_distribution.amount)}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Next Distribution */}
      <div className="next-distribution">
        <h3>⏰ Next Distribution</h3>
        <div className="next-date">{yieldData?.next_distribution_date || 'Calculating...'}</div>
        <p className="note">Yield is distributed hourly based on your token holdings</p>
      </div>

      {/* RECENT DISTRIBUTIONS - The main fix */}
      <div className="recent-distributions-section">
        <h3>📋 Recent Distributions</h3>
        {distributions.length === 0 ? (
          <div className="empty-state">
            <p>No distributions yet. Your yield will appear here after the next hourly distribution.</p>
          </div>
        ) : (
          <div className="distributions-table">
            <div className="table-header">
              <div className="header-token">Token</div>
              <div className="header-amount">Amount (USDC)</div>
              <div className="header-date">Date & Time</div>
            </div>
            {distributions.slice(0, 20).map((dist, index) => (
              <div key={dist.id || index} className="distribution-row">
                <div className="row-token">
                  <span className="token-badge">{dist.token}</span>
                </div>
                <div className="row-amount profit">+${dist.amount.toFixed(6)}</div>
                <div className="row-date">{new Date(dist.date).toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="yield-stats">
        <div className="stat">
          <span>📈 Total Distributions:</span>
          <strong>{distributions.length}</strong>
        </div>
        <div className="stat">
          <span>⏱️ Frequency:</span>
          <strong>Hourly</strong>
        </div>
      </div>

      {/* Refresh Button */}
      <button onClick={fetchYieldData} className="refresh-btn">
        🔄 Refresh Data
      </button>
    </div>
  );
}

export default YieldDashboard;
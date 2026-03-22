import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import './YieldDashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

function YieldDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [hourlyDistributions, setHourlyDistributions] = useState([]);
  const [yieldBalances, setYieldBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState('area'); // 'area', 'line', 'bar'
  const [timeframe, setTimeframe] = useState('hourly'); // 'hourly', 'daily', 'weekly'

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const statsResponse = await axios.get(`${API_URL}/volatility/yield/stats/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setStats(statsResponse.data);

      const hourlyResponse = await axios.get(`${API_URL}/volatility/yield/hourly/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setHourlyDistributions(hourlyResponse.data);

      const balanceResponse = await axios.get(`${API_URL}/volatility/yield/balance/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setYieldBalances(balanceResponse.data);

    } catch (error) {
      console.error('Error fetching yield data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);
  };

  // Prepare chart data
  const getChartData = () => {
    if (timeframe === 'hourly') {
      return hourlyDistributions.slice().reverse().slice(-24).map(d => ({
        time: new Date(d.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        amount: d.amount,
        token: d.token
      }));
    } else if (timeframe === 'daily') {
      // Group by day
      const dailyMap = new Map();
      hourlyDistributions.forEach(d => {
        const day = new Date(d.date).toLocaleDateString([], { month: 'short', day: 'numeric' });
        if (dailyMap.has(day)) {
          dailyMap.set(day, dailyMap.get(day) + d.amount);
        } else {
          dailyMap.set(day, d.amount);
        }
      });
      return Array.from(dailyMap.entries()).map(([day, amount]) => ({
        time: day,
        amount: amount
      }));
    } else {
      // Weekly - group by week
      const weeklyMap = new Map();
      hourlyDistributions.forEach(d => {
        const date = new Date(d.date);
        const week = `Week ${Math.ceil(date.getDate() / 7)}`;
        if (weeklyMap.has(week)) {
          weeklyMap.set(week, weeklyMap.get(week) + d.amount);
        } else {
          weeklyMap.set(week, d.amount);
        }
      });
      return Array.from(weeklyMap.entries()).map(([week, amount]) => ({
        time: week,
        amount: amount
      }));
    }
  };

  // Get token distribution for bar chart
  const getTokenChartData = () => {
    return yieldBalances
      .filter(t => t.yield_balance > 0)
      .map(token => ({
        name: token.token_symbol,
        value: token.yield_balance
      }));
  };

  const chartData = getChartData();
  const tokenChartData = getTokenChartData();

  const renderChart = () => {
    if (chartData.length === 0) {
      return <div className="chart-placeholder">No data available</div>;
    }

    if (chartType === 'bar') {
      return (
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis tickFormatter={(value) => `$${value.toFixed(4)}`} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
          <Bar dataKey="amount" fill="#10b981" name="Yield Amount" />
        </BarChart>
      );
    } else if (chartType === 'line') {
      return (
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis tickFormatter={(value) => `$${value.toFixed(4)}`} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
          <Line type="monotone" dataKey="amount" stroke="#2563eb" strokeWidth={2} dot={false} name="Yield Amount" />
        </LineChart>
      );
    } else {
      return (
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis tickFormatter={(value) => `$${value.toFixed(4)}`} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
          <Area type="monotone" dataKey="amount" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.3} name="Yield Amount" />
        </AreaChart>
      );
    }
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
      <div className="no-yield-message">
        <p>Error: {error}</p>
        <button onClick={fetchAllData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="yield-dashboard">
      <div className="yield-header">
        <h2>Yield Dashboard</h2>
        <p className="yield-subtitle">Track your volatility token earnings</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">💰 Total Yield Earned</span>
          <div className="stat-value">{formatCurrency(stats?.total_yield_earned || 0)}</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">📊 Current Portfolio Value</span>
          <div className="stat-value">{formatCurrency(stats?.current_value || 0)}</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">🌱 Projected Annual Yield</span>
          <div className="stat-range">
            {formatCurrency(stats?.projected_annual_yield?.min || 0)}
            <span className="separator"> - </span>
            {formatCurrency(stats?.projected_annual_yield?.max || 0)}
          </div>
          <div className="sub-text">8-10% of portfolio value</div>
        </div>
      </div>

      {/* Yield Over Time Chart */}
      <div className="chart-section">
        <div className="chart-header">
          <h3>📈 Yield Over Time</h3>
          <div className="chart-controls">
            <button
              className={chartType === 'area' ? 'active' : ''}
              onClick={() => setChartType('area')}
            >
              Area
            </button>
            <button
              className={chartType === 'line' ? 'active' : ''}
              onClick={() => setChartType('line')}
            >
              Line
            </button>
            <button
              className={chartType === 'bar' ? 'active' : ''}
              onClick={() => setChartType('bar')}
            >
              Bar
            </button>
          </div>
        </div>
        <div className="chart-timeframe">
          <button
            className={timeframe === 'hourly' ? 'active' : ''}
            onClick={() => setTimeframe('hourly')}
          >
            Hourly
          </button>
          <button
            className={timeframe === 'daily' ? 'active' : ''}
            onClick={() => setTimeframe('daily')}
          >
            Daily
          </button>
          <button
            className={timeframe === 'weekly' ? 'active' : ''}
            onClick={() => setTimeframe('weekly')}
          >
            Weekly
          </button>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Token Distribution Bar Chart */}
      {tokenChartData.length > 0 && (
        <div className="chart-section">
          <h3>📊 Yield by Token</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tokenChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(value) => `$${value.toFixed(4)}`} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="value" fill="#10b981" name="Yield Balance" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Last Distribution */}
      {hourlyDistributions.length > 0 && (
        <div className="last-distribution-card">
          <h3>📅 Last Distribution</h3>
          <div className="distribution-details">
            <div className="detail-item">
              <span>Date:</span>
              <strong>{new Date(hourlyDistributions[0].date).toLocaleString()}</strong>
            </div>
            <div className="detail-item">
              <span>Token:</span>
              <strong>{hourlyDistributions[0].token}</strong>
            </div>
            <div className="detail-item">
              <span>Amount:</span>
              <strong className="profit">+{formatCurrency(hourlyDistributions[0].amount)}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Next Distribution */}
      <div className="next-distribution-card">
        <h3>⏰ Next Distribution</h3>
        <div className="next-date">
          {new Date(Date.now() + 3600000).toLocaleString()}
        </div>
        <p className="note">Yield is distributed hourly based on your token holdings</p>
      </div>

      {/* Recent Distributions */}
      <div className="distributions-section">
        <h3>📋 Recent Distributions</h3>
        {hourlyDistributions.length === 0 ? (
          <div className="empty-state">
            <p>No distributions yet</p>
            <p className="small">Your yield will appear here after the next hourly distribution</p>
          </div>
        ) : (
          <div className="distributions-table">
            <div className="table-header">
              <div>Token</div>
              <div>Amount</div>
              <div>Date & Time</div>
            </div>
            {hourlyDistributions.slice(0, 10).map((dist, index) => (
              <div key={dist.id || index} className="distribution-row">
                <div><span className="token-badge">{dist.token}</span></div>
                <div className="row-amount">+{formatCurrency(dist.amount)}</div>
                <div className="row-date">{new Date(dist.date).toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Yield by Token Cards */}
      <div className="yield-token-section">
        <h3>💎 Yield by Token</h3>
        <div className="yield-balance-grid">
          {yieldBalances.length === 0 ? (
            <div className="no-yield-message">
              <p>No yield balances yet</p>
            </div>
          ) : (
            yieldBalances.map((token) => (
              <div key={token.token_id} className="yield-balance-card">
                <div className="yield-balance-header">
                  <span className="token-symbol">{token.token_symbol}</span>
                  <span className="token-name">{token.token_name}</span>
                </div>
                <div className="yield-value">{formatCurrency(token.yield_balance)}</div>
                <div className="yield-details">
                  <div className="detail-row">
                    <span>Total Earned:</span>
                    <span>{formatCurrency(token.yield_earned_total)}</span>
                  </div>
                  <div className="detail-row">
                    <span>Current Value:</span>
                    <span>{formatCurrency(token.current_value)}</span>
                  </div>
                </div>
                <button
                  className="withdraw-btn"
                  disabled={token.yield_balance <= 0}
                  onClick={() => {
                    // Withdraw functionality
                  }}
                >
                  Withdraw Yield
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Live Feed Section */}
      <div className="live-feed-section">
        <h3>🔴 Live Yield Feed</h3>
        <div className="live-feed">
          {hourlyDistributions.slice(0, 5).map((dist, index) => (
            <div key={index} className="feed-item">
              <span className="feed-time">{new Date(dist.date).toLocaleTimeString()}</span>
              <span className="feed-token">{dist.token}</span>
              <span className="feed-amount">+{formatCurrency(dist.amount)}</span>
            </div>
          ))}
          {hourlyDistributions.length === 0 && (
            <div className="empty-state">Waiting for distributions...</div>
          )}
        </div>
      </div>

      {/* Stats Footer */}
      <div className="yield-stats">
        <div className="stat">
          <span>Total Distributions</span>
          <strong>{hourlyDistributions.length}</strong>
        </div>
        <div className="stat">
          <span>Distribution Frequency</span>
          <strong>Hourly</strong>
        </div>
      </div>

      <button onClick={fetchAllData} className="refresh-btn">
        🔄 Refresh Data
      </button>
    </div>
  );
}

export default YieldDashboard;
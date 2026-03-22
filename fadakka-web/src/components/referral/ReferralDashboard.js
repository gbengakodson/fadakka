import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import './ReferralDashboard.css';

const ReferralDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [networkData, setNetworkData] = useState(null);
  const [earningsData, setEarningsData] = useState(null);
  const [downlinesData, setDownlinesData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [treeData, setTreeData] = useState(null);

  // Filter states
  const [earningsLevel, setEarningsLevel] = useState('all');
  const [earningsDays, setEarningsDays] = useState(30);
  const [treeDepth, setTreeDepth] = useState(3);

  const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch all referral data in parallel
      const [network, earnings, downlines, stats, tree] = await Promise.all([
        axios.get('/api/referral/network/'),
        axios.get('/api/referral/earnings/'),
        axios.get('/api/referral/downlines/'),
        axios.get('/api/referral/stats/'),
        axios.get('/api/referral/tree/?depth=3')
      ]);

      setNetworkData(network.data);
      setEarningsData(earnings.data);
      setDownlinesData(downlines.data);
      setStatsData(stats.data);
      setTreeData(tree.data);
    } catch (err) {
      console.error('Error fetching referral data:', err);
      setError('Failed to load referral data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchEarningsWithFilters = async () => {
    try {
      const params = new URLSearchParams();
      if (earningsLevel !== 'all') params.append('level', earningsLevel);
      params.append('days', earningsDays);

      const response = await axios.get(`/api/referral/earnings/?${params.toString()}`);
      setEarningsData(response.data);
    } catch (err) {
      console.error('Error fetching filtered earnings:', err);
    }
  };

  const copyReferralLink = () => {
    if (networkData?.referral_link) {
      navigator.clipboard.writeText(networkData.referral_link);
      alert('Referral link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">⚠️</div>
        <h3>Error Loading Data</h3>
        <p>{error}</p>
        <button onClick={fetchAllData} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="referral-dashboard">
      {/* Header with Referral Link */}
      <div className="dashboard-header">
        <h1>BlockNode</h1>
        <div className="referral-link-box">
          <div className="referral-code">
            <span className="label">Hash Code:</span>
            <span className="code">{networkData?.referral_code}</span>
          </div>
          <div className="referral-link-input">
            <input
              type="text"
              value={networkData?.referral_link || ''}
              readOnly
            />
            <button onClick={copyReferralLink} className="copy-btn">
              📋 Copy Link
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card total-earned">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <span className="stat-label">Total Earned</span>
            <span className="stat-value">${networkData?.total_earned?.toFixed(2) || '0.00'}</span>
          </div>
        </div>

        <div className="stat-card pending">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <span className="stat-label">Pending</span>
            <span className="stat-value">${networkData?.pending_earnings?.toFixed(2) || '0.00'}</span>
          </div>
        </div>

        <div className="stat-card active-referrals">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <span className="stat-label">Active</span>
            <span className="stat-value">{networkData?.active_referrals || 0}</span>
          </div>
        </div>

        <div className="stat-card conversion">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <span className="stat-label">Conversion Rate</span>
            <span className="stat-value">{networkData?.conversion_rate || 0}%</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="tabs-navigation">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'earnings' ? 'active' : ''}`}
          onClick={() => setActiveTab('earnings')}
        >
          Earnings
        </button>
        <button
          className={`tab-btn ${activeTab === 'downlines' ? 'active' : ''}`}
          onClick={() => setActiveTab('downlines')}
        >
          Node Layer
        </button>
        <button
          className={`tab-btn ${activeTab === 'tree' ? 'active' : ''}`}
          onClick={() => setActiveTab('tree')}
        >
          Hash Tree
        </button>
        <button
          className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="charts-row">
              <div className="chart-card">
                <h3>Monthly Earnings</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={networkData?.monthly_earnings || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="amount" stroke="#4F46E5" fill="#4F46E566" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-card">
                <h3>Node Layers</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(networkData?.downlines || {}).map(([level, count]) => ({
                        name: level.replace('_', ' ').toUpperCase(),
                        value: count
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(networkData?.downlines || {}).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="recent-earnings">
              <h3>Recent Earnings</h3>
              <table className="earnings-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>From</th>
                    <th>Level</th>
                    <th>Node Fee</th>
                    <th>Return</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {networkData?.recent_earnings?.map((earning, index) => (
                    <tr key={index}>
                      <td>{earning.date}</td>
                      <td>{earning.from}</td>
                      <td>
                        <span className={`level-badge level-${earning.level}`}>
                          Layer {earning.level}
                        </span>
                      </td>
                      <td>${earning.node_fee?.toFixed(2)}</td>
                      <td>{earning.percentage}%</td>
                      <td className="amount positive">+${earning.amount?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Earnings Tab */}
        {activeTab === 'earnings' && (
          <div className="earnings-tab">
            <div className="filters-bar">
              <div className="filter-group">
                <label>Layer:</label>
                <select value={earningsLevel} onChange={(e) => setEarningsLevel(e.target.value)}>
                  <option value="all">All Layers</option>
                  <option value="1">Layer 1</option>
                  <option value="2">Layer 2</option>
                  <option value="3">Layer 3</option>
                  <option value="4">Layer 4</option>
                  <option value="5">Layer 5</option>
                  <option value="6">Layer 6</option>
                  <option value="7">Layer 7</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Days:</label>
                <select value={earningsDays} onChange={(e) => setEarningsDays(e.target.value)}>
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">Last year</option>
                </select>
              </div>

              <button onClick={fetchEarningsWithFilters} className="apply-filters-btn">
                Apply Filters
              </button>
            </div>

            <div className="earnings-breakdown">
              <h3>Earnings by Level</h3>
              <div className="level-bars">
                {earningsData?.level_breakdown?.map((level) => (
                  <div key={level.level} className="level-bar-item">
                    <div className="level-label">Level {level.level}</div>
                    <div className="bar-container">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(level.total / earningsData.total_earned) * 100}%`,
                          backgroundColor: COLORS[level.level - 1]
                        }}
                      ></div>
                      <span className="bar-value">${level.total.toFixed(2)}</span>
                    </div>
                    <div className="level-count">{level.count} transactions</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="recent-transactions">
              <h3>Transaction History</h3>
              <table className="transactions-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>From</th>
                    <th>Level</th>
                    <th>Token</th>
                    <th>Node Fee</th>
                    <th>Return %</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {earningsData?.recent_transactions?.map((tx) => (
                    <tr key={tx.id}>
                      <td>{tx.date}</td>
                      <td>{tx.from_user}</td>
                      <td>
                        <span className={`level-badge level-${tx.level}`}>
                          Level {tx.level}
                        </span>
                      </td>
                      <td>{tx.token}</td>
                      <td>${tx.node_fee?.toFixed(2)}</td>
                      <td>{tx.percentage}%</td>
                      <td className="amount positive">+${tx.amount?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Downlines Tab */}
        {activeTab === 'downlines' && (
          <div className="downlines-tab">
            <h3>Your Node Layer</h3>
            <div className="downlines-summary">
              <div className="summary-card">
                <span className="summary-label">Total</span>
                <span className="summary-value">{downlinesData?.total_downlines || 0}</span>
              </div>
            </div>

            <div className="downlines-by-level">
              {[1,2,3,4,5,6,7].map(level => (
                <div key={level} className="level-section">
                  <h4>Layer {level} - {downlinesData?.downlines?.[`level_${level}`]?.length || 0} users</h4>
                  <div className="users-grid">
                    {downlinesData?.downlines?.[`level_${level}`]?.map(user => (
                      <div key={user.id} className="user-card">
                        <div className="user-avatar">
                          {user.username.charAt(0).toUpperCase()}
                        </div>
                        <div className="user-info">
                          <span className="username">{user.username}</span>
                          <span className="user-email">{user.email}</span>
                          <span className="user-joined">Joined: {user.joined}</span>
                          {user.active && <span className="active-badge">Active</span>}
                        </div>
                        <div className="user-earnings">
                          <span className="earnings-label">Generated:</span>
                          <span className="earnings-value">${user.earnings?.toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tree Tab */}
        {activeTab === 'tree' && (
          <div className="tree-tab">
            <div className="tree-controls">
              <label>Tree Depth:</label>
              <select value={treeDepth} onChange={(e) => setTreeDepth(e.target.value)}>
                <option value="2">2 Layers</option>
                <option value="3">3 Layers</option>
                <option value="4">4 Layers</option>
              </select>
            </div>

            <div className="referral-tree-container">
              {treeData && <ReferralTreeNode node={treeData} level={0} />}
            </div>
          </div>
        )}

        {/* Stats Tab */}
        {activeTab === 'stats' && (
          <div className="stats-tab">
            <div className="stats-grid-detailed">
              <div className="stat-detailed-card">
                <h4>Level Breakdown</h4>
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>Layer</th>
                      <th>Count</th>
                      <th>Earnings</th>
                      <th>Return</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[1,2,3,4,5,6,7].map(level => (
                      <tr key={level}>
                        <td>Level {level}</td>
                        <td>{statsData?.level_breakdown?.[`level_${level}_count`] || 0}</td>
                        <td>${statsData?.level_breakdown?.[`level_${level}_earnings`]?.toFixed(2) || '0.00'}</td>
                        <td>{statsData?.commission_rates?.find(r => r.level === level)?.rate || 0}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="stat-detailed-card">
                <h4>Performance Metrics</h4>
                <div className="metrics-list">
                  <div className="metric-item">
                    <span className="metric-label">Earnings (7 days):</span>
                    <span className="metric-value">${statsData?.earnings_week?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Earnings (30 days):</span>
                    <span className="metric-value">${statsData?.earnings_month?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Click-through rate:</span>
                    <span className="metric-value">{networkData?.click_stats?.total_clicks || 0} clicks</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Unique clicks:</span>
                    <span className="metric-value">{networkData?.click_stats?.unique_clicks || 0}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Conversions:</span>
                    <span className="metric-value">{networkData?.click_stats?.conversions || 0}</span>
                  </div>
                </div>
              </div>

              <div className="stat-detailed-card">
                <h4>Node Layer Performance</h4>
                <div className="leaderboard-info">
                  <div className="rank-circle">
                    <span className="rank-number">#{networkData?.leaderboard_position?.position || 'N/A'}</span>
                    <span className="rank-total">of {networkData?.leaderboard_position?.total_referrers || 0}</span>
                  </div>
                  <p>Top {((networkData?.leaderboard_position?.position / networkData?.leaderboard_position?.total_referrers) * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div className="top-referrers">
              <h4>Top Networks This Month</h4>
              <div className="top-referrers-list">
                {statsData?.top_referrers?.map((referrer, index) => (
                  <div key={index} className="top-referrer-item">
                    <span className="rank">{index + 1}</span>
                    <span className="name">{referrer.username}</span>
                    <span className="count">{referrer.referrals} referrals</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Tree Node Component for rendering the referral tree
const ReferralTreeNode = ({ node, level }) => {
  const [expanded, setExpanded] = useState(true);

  if (!node) return null;

  return (
    <div className={`tree-node level-${level}`}>
      <div className="node-content" onClick={() => setExpanded(!expanded)}>
        <div className="node-avatar">
          {node.name?.charAt(0).toUpperCase()}
        </div>
        <div className="node-details">
          <span className="node-name">{node.name}</span>
          <span className="node-code">{node.code}</span>
          <span className="node-earnings">${node.earnings?.toFixed(2)}</span>
        </div>
        {node.children?.length > 0 && (
          <button className="expand-btn">
            {expanded ? '▼' : '▶'}
          </button>
        )}
      </div>

      {expanded && node.children?.length > 0 && (
        <div className="node-children">
          {node.children.map((child, index) => (
            <ReferralTreeNode key={index} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ReferralDashboard;
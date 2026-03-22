import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Dashboard.css';
import DepositModal from '../components/wallet/DepositModal';
import WithdrawalModal from '../components/wallet/WithdrawalModal';
import KYCStatus from '../components/kyc/KYCStatus';
import KYCSumbitForm from '../components/kyc/KYCSumbitForm';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';


// BlockNodeReturns Component - Added directly in this file
const BlockNodeReturns = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [referralData, setReferralData] = useState({
    total_earned: 0,
    pending_earnings: 0,
    level_breakdown: [],
    recent_earnings: [],
    referral_code: '',
    referral_link: ''
  });
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchBlockNodeReturns();
  }, []);

  const fetchBlockNodeReturns = async () => {
    try {
      const response = await axios.get(`${API_URL}/referral/network/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const earningsResponse = await axios.get(`${API_URL}/referral/earnings/?days=30`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setReferralData({
        total_earned: response.data.total_earned || 0,
        pending_earnings: response.data.pending_earnings || 0,
        referral_code: response.data.referral_code || 'N/A',
        referral_link: response.data.referral_link || '',
        conversion_rate: response.data.conversion_rate || 0,
        level_breakdown: earningsResponse.data.level_breakdown || [],
        recent_earnings: (response.data.recent_earnings || []).slice(0, 5)
      });
    } catch (err) {
      console.error('Error fetching block-node returns:', err);
      setError('Could not load returns data');
    } finally {
      setLoading(false);
    }
  };

  const copyReferralCode = () => {
    if (referralData.referral_code) {
      navigator.clipboard.writeText(referralData.referral_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="block-node-loading">
        <div className="loading-spinner-small"></div>
        <span>Loading returns...</span>
      </div>
    );
  }

  return (
    <div className="block-node-returns-card">
      <div className="block-node-header" onClick={() => setShowDetails(!showDetails)}>
        <div className="header-left">
          <div className="header-icon">🔷</div>
          <div>
            <h3>Block-Node Returns</h3>
            <p className="header-subtitle">7-Generation referral earnings</p>
          </div>
        </div>
        <div className="header-right">
          <div className="total-returns">
            <span className="returns-label">Total Earned</span>
            <span className="returns-value">${referralData.total_earned.toFixed(2)}</span>
          </div>
          <button className="expand-btn">
            {showDetails ? '▼' : '▶'}
          </button>
        </div>
      </div>

      <div className="quick-stats">
        <div className="stat-item">
          <span className="stat-label">Pending</span>
          <span className="stat-value">${referralData.pending_earnings.toFixed(2)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">This Month</span>
          <span className="stat-value">
            ${referralData.level_breakdown.reduce((sum, level) => sum + level.total, 0).toFixed(2)}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Conv. Rate</span>
          <span className="stat-value">{referralData.conversion_rate}%</span>
        </div>
      </div>

      <div className="referral-code-section">
        <div className="code-display">
          <span className="code-label">Your Code:</span>
          <span className="code-value">{referralData.referral_code}</span>
          <button
            className={`copy-btn-small ${copied ? 'copied' : ''}`}
            onClick={copyReferralCode}
            title="Copy referral code"
          >
            {copied ? '✓' : '📋'}
          </button>
        </div>
      </div>

      {showDetails && (
        <div className="block-node-details">
          <div className="level-breakdown">
            <h4>Returns by Level (30 days)</h4>
            <div className="level-bars">
              {[1,2,3,4,5,6,7].map(level => {
                const levelData = referralData.level_breakdown.find(l => l.level === level) || { total: 0, count: 0 };
                const total = referralData.level_breakdown.reduce((sum, l) => sum + l.total, 0);
                const percentage = total > 0 ? (levelData.total / total) * 100 : 0;

                return (
                  <div key={level} className="level-item">
                    <div className="level-info">
                      <span className="level-number">Level {level}</span>
                      <span className="level-percent">
                        {level === 1 ? '100%' :
                         level === 2 ? '20%' :
                         level === 3 ? '10%' :
                         level === 4 ? '7%' :
                         level === 5 ? '5%' :
                         level === 6 ? '3%' : '1%'}
                      </span>
                    </div>
                    <div className="level-bar-container">
                      <div
                        className="level-bar"
                        style={{
                          width: `${percentage}%`,
                          backgroundColor:
                            level === 1 ? '#2563eb' :
                            level === 2 ? '#10b981' :
                            level === 3 ? '#f59e0b' :
                            level === 4 ? '#ef4444' :
                            level === 5 ? '#8b5cf6' :
                            level === 6 ? '#ec4899' : '#14b8a6'
                        }}
                      ></div>
                      <span className="level-amount">${levelData.total.toFixed(2)}</span>
                    </div>
                    <span className="level-count">{levelData.count} transactions</span>
                  </div>
                );
              })}
            </div>
          </div>

          {referralData.recent_earnings.length > 0 && (
            <div className="recent-returns">
              <h4>Recent Returns</h4>
              <div className="returns-list">
                {referralData.recent_earnings.map((earning, index) => (
                  <div key={index} className="return-item">
                    <div className="return-info">
                      <span className="return-from">{earning.from}</span>
                      <span className={`return-level level-${earning.level}`}>
                        L{earning.level}
                      </span>
                    </div>
                    <div className="return-details">
                      <span className="return-date">{earning.date}</span>
                      <span className="return-amount">+${earning.amount?.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="how-it-works">
            <h4>How Block-Node Returns Work</h4>
            <ul className="explanation-list">
              <li>🔷 <strong>10% node fee</strong> from every purchase</li>
              <li>👥 <strong>7 generations</strong> of referrals share this fee</li>
              <li>📊 <strong>Commission:</strong> 100% → 20% → 10% → 7% → 5% → 3% → 1%</li>
              <li>⏰ Returns credited instantly when referrals trade</li>
            </ul>
          </div>

          <div className="share-section">
            <h4>Share Your Code</h4>
            <div className="share-buttons">
              <a
                href={`https://wa.me/?text=Join%20Fadakka%20using%20my%20referral%20code%3A%20${referralData.referral_code}`}
                target="_blank"
                rel="noopener noreferrer"
                className="share-btn whatsapp"
              >
                WhatsApp
              </a>
              <a
                href={`https://t.me/share/url?url=${encodeURIComponent(referralData.referral_link)}&text=Join%20Fadakka%20using%20my%20referral%20code`}
                target="_blank"
                rel="noopener noreferrer"
                className="share-btn telegram"
              >
                Telegram
              </a>
              <a
                href={`https://twitter.com/intent/tweet?text=Join%20Fadakka%20with%20my%20referral%20code%3A%20${referralData.referral_code}&url=${encodeURIComponent(referralData.referral_link)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="share-btn twitter"
              >
                Twitter
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [balance, setBalance] = useState(0);
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [recentOrders, setRecentOrders] = useState([]);

  // Modal states
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [showKYCForm, setShowKYCForm] = useState(false);

  // Check for KYC parameter in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('kyc') === 'true') {
      setShowKYCForm(true);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch GrandBalance
      const balanceResponse = await axios.get(`${API_URL}/wallet/grand-balance/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setBalance(Number(balanceResponse.data.balance_usdc) || 0);

      // Fetch token holdings
      const holdingsResponse = await axios.get(`${API_URL}/volatility/user-tokens/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      console.log('Holdings response:', holdingsResponse.data);

      // Process holdings correctly - data is directly in the holding object
      const processedHoldings = holdingsResponse.data.map(holding => ({
        id: holding.id,
        balance: Number(holding.balance) || 0,
        token_symbol: holding.token_symbol || 'Unknown',
        token_name: holding.token_name || '',
        current_price: Number(holding.current_price) || 0,
        coin_id: holding.token || ''  // token ID for navigation
      }));

      setHoldings(processedHoldings);

      // Calculate portfolio value
      const total = processedHoldings.reduce((sum, h) => {
        return sum + (h.balance * h.current_price);
      }, 0);
      setPortfolioValue(total);

      // Fetch recent orders
      const ordersResponse = await axios.get(`${API_URL}/volatility/orders/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      const processedOrders = ordersResponse.data.slice(0, 5).map(order => ({
        ...order,
        amount: Number(order.amount) || 0,
        price: Number(order.price) || 0,
        total: Number(order.total) || 0,
        token_symbol: order.token_symbol || 'Unknown'
      }));

      setRecentOrders(processedOrders);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatCurrency = (value) => {
    const numValue = Number(value) || 0;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(numValue);
  };

  const formatTokenAmount = (value) => {
    const numValue = Number(value) || 0;
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 4,
      maximumFractionDigits: 8
    }).format(numValue);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Helper function to get coin ID from token symbol for navigation
  const getCoinIdFromSymbol = (tokenSymbol) => {
    const symbolMap = {
      'BTC-VT': 'bitcoin',
      'ETH-VT': 'ethereum',
      'ADA-VT': 'cardano',
      'XRP-VT': 'ripple',
      'LINK-VT': 'chainlink',
      'SUI-VT': 'sui',
      'PEPE-VT': 'pepe',
      'SOL-VT': 'solana',
      'BNB-VT': 'binancecoin'
    };
    return symbolMap[tokenSymbol] || tokenSymbol.replace('-VT', '').toLowerCase();
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Navigation Bar */}
      <nav className="dashboard-nav">
        <div className="nav-left">
          <h1 className="nav-logo">Node!...market volatility at your own advantage</h1>
        </div>
        <div className="nav-right">
          <span className="nav-user">Welcome, {user?.username}</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        <h1>Your Dashboard</h1>

        {/* QUICK ACTION BUTTONS - Easy navigation */}
        <div className="quick-actions">
          <button
            className="action-btn primary"
            onClick={() => navigate('/portfolio')}
          >
            📊 View Portfolio
          </button>
          <button
            className="action-btn secondary"
            onClick={() => navigate('/transactions')}
          >
            📜 Transaction History
          </button>
          <button
            className="action-btn success"
            onClick={() => navigate('/')}
          >
            🪙 Trade Coins
          </button>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <h3>GrandBalance</h3>
              <p className="stat-value">{formatCurrency(balance)}</p>

              {/* Withdrawal limit info */}
              <div className="withdrawal-limit">
                <small>Daily withdrawal limit: </small>
                <strong className={balance > 0 ? 'limit-active' : ''}>
                  {user?.kyc_verified ? '$50,000' : '$1,000'}
                </strong>
                {!user?.kyc_verified && balance > 0 && (
                  <button
                    className="kyc-upgrade-btn"
                    onClick={() => setShowKYCForm(true)}
                  >
                    Upgrade
                  </button>
                )}
              </div>

              <div className="balance-actions">
                <button
                  onClick={() => {
                    console.log('💰 Deposit button clicked');
                    setShowDepositModal(true);
                  }}
                  className="stat-action deposit"
                >
                  + Deposit
                </button>
                <button
                  onClick={() => {
                    console.log('💰 Withdraw button clicked, balance:', balance);
                    setShowWithdrawModal(true);
                  }}
                  className="stat-action withdraw"
                  disabled={balance <= 0}
                >
                  - Withdraw
                </button>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <h3>Portfolio Value</h3>
              <p className="stat-value">{formatCurrency(portfolioValue)}</p>
              <small className="stat-note">
                {holdings.length} token{holdings.length !== 1 ? 's' : ''}
              </small>
              <button
                className="stat-action small"
                onClick={() => navigate('/portfolio')}
              >
                View Details →
              </button>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💎</div>
            <div className="stat-content">
              <h3>Total Assets</h3>
              <p className="stat-value">{formatCurrency((balance || 0) + portfolioValue)}</p>
              <small className="stat-note">GrandBalance + Portfolio</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <h3>Recent Orders</h3>
              <p className="stat-value">{recentOrders.length}</p>
              <small className="stat-note">Last 5 transactions</small>
              <button
                className="stat-action small"
                onClick={() => navigate('/transactions')}
              >
                View All →
              </button>
            </div>
          </div>
        </div>

        <BlockNodeReturns />

        {/* KYC Status Section */}
        <KYCStatus onOpenForm={() => setShowKYCForm(true)} />

        {/* Holdings Summary */}
        {holdings.length > 0 && (
          <div className="holdings-section">
            <div className="section-header">
              <h2>Your Top Holdings</h2>
              <button
                className="view-all-link"
                onClick={() => navigate('/portfolio')}
              >
                View Full Portfolio →
              </button>
            </div>
            <div className="holdings-grid">
              {holdings.slice(0, 3).map((holding) => {
                const holdingValue = holding.balance * holding.current_price;
                const coinId = getCoinIdFromSymbol(holding.token_symbol);

                return (
                  <div key={holding.id} className="holding-card">
                    <div className="holding-header">
                      <span className="holding-symbol">{holding.token_symbol}</span>
                      <span className="holding-name">{holding.token_name}</span>
                    </div>
                    <div className="holding-details">
                      <div className="holding-row">
                        <span>Balance:</span>
                        <span className="holding-amount">{formatTokenAmount(holding.balance)}</span>
                      </div>
                      <div className="holding-row">
                        <span>Value:</span>
                        <span className="holding-value">{formatCurrency(holdingValue)}</span>
                      </div>
                    </div>
                    <button
                      className="trade-link"
                      onClick={() => navigate(`/trade/${coinId}`)}
                    >
                      Trade More →
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent Activity */}
        {recentOrders.length > 0 && (
          <div className="recent-activity">
            <div className="section-header">
              <h2>Recent Transactions</h2>
              <button
                className="view-all-link"
                onClick={() => navigate('/transactions')}
              >
                View All →
              </button>
            </div>
            <div className="activity-list">
              {recentOrders.map((order) => (
                <div key={order.id} className="activity-item">
                  <div className="activity-icon">
                    {order.order_type === 'buy' ? '🟢' : '🔴'}
                  </div>
                  <div className="activity-details">
                    <div className="activity-header">
                      <span className={`activity-type ${order.order_type}`}>
                        {order.order_type?.toUpperCase() || 'VT'}
                      </span>
                      <span className="activity-token">{order.token_symbol || 'vt'}</span>
                    </div>
                    <div className="activity-meta">
                      <span className="activity-amount">
                        {formatTokenAmount(order.amount)} tokens
                      </span>
                      <span className="activity-price">
                        @ {formatCurrency(order.price)}
                      </span>
                      <span className="activity-total">
                        {formatCurrency(order.total)}
                      </span>
                    </div>
                  </div>
                  <div className="activity-time">
                    {formatDate(order.created_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {holdings.length === 0 && recentOrders.length === 0 && (
          <div className="empty-state">
            <p>Node!</p>
            <p className="empty-sub">Start by depositing funds and trading crypto volatility tokens.</p>
            <button
              className="start-trading-btn"
              onClick={() => navigate('/')}
            >
              Start Trading
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      <DepositModal
        isOpen={showDepositModal}
        onClose={() => setShowDepositModal(false)}
        onSuccess={() => {
          fetchDashboardData();
          setShowDepositModal(false);
        }}
      />

      <WithdrawalModal
        isOpen={showWithdrawModal}
        onClose={() => setShowWithdrawModal(false)}
        onSuccess={(data) => {
          fetchDashboardData();
          setShowWithdrawModal(false);
          alert(`✅ Withdrawal successful! New balance: $${data.new_balance}`);
        }}
        maxAmount={balance}
      />

      {/* KYC Form Modal */}
      {showKYCForm && (
        <KYCSumbitForm
          onClose={() => setShowKYCForm(false)}
          onSuccess={() => {
            setShowKYCForm(false);
            fetchDashboardData();
          }}
        />
      )}
    </div>
  );
}

export default Dashboard;
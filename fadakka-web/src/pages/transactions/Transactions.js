import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Transactions.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

function Transactions() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [tokenFilter, setTokenFilter] = useState('all');
  const [tokens, setTokens] = useState([]);
  const [stats, setStats] = useState({
    totalBuy: 0,
    totalSell: 0,
    totalSpent: 0,
    totalReceived: 0,
    totalFees: 0
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
    fetchOrders();
    fetchTokens();
  }, [isAuthenticated, navigate]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/volatility/orders/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      // Ensure all numeric values are properly converted to numbers
      const processedOrders = response.data.map(order => ({
        ...order,
        amount: Number(order.amount) || 0,
        price: Number(order.price) || 0,
        total: Number(order.total) || 0
      }));

      setOrders(processedOrders);
      calculateStats(processedOrders);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTokens = async () => {
    try {
      const response = await axios.get(`${API_URL}/volatility/tokens/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setTokens(response.data);
    } catch (error) {
      console.error('Error fetching tokens:', error);
    }
  };

  const calculateStats = (orderData) => {
    const buyOrders = orderData.filter(o => o.order_type === 'buy');
    const sellOrders = orderData.filter(o => o.order_type === 'sell');

    const totalBuy = buyOrders.reduce((sum, o) => sum + (Number(o.amount) || 0), 0);
    const totalSell = sellOrders.reduce((sum, o) => sum + (Number(o.amount) || 0), 0);
    const totalSpent = buyOrders.reduce((sum, o) => sum + (Number(o.total) || 0), 0);
    const totalReceived = sellOrders.reduce((sum, o) => sum + (Number(o.total) || 0), 0);
    const totalFees = orderData.reduce((sum, o) => sum + (Number(o.fee) || 0), 0);

    setStats({
      totalBuy,
      totalSell,
      totalSpent,
      totalReceived,
      totalFees
    });
  };

  const getFilteredOrders = () => {
    let filtered = orders;

    if (filter !== 'all') {
      filtered = filtered.filter(o => o.order_type === filter);
    }

    if (tokenFilter !== 'all') {
      filtered = filtered.filter(o => o.token === parseInt(tokenFilter));
    }

    return filtered;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

  const getTokenSymbol = (tokenId) => {
    const token = tokens.find(t => t.id === tokenId);
    return token ? token.token_symbol : 'Unknown';
  };

  const filteredOrders = getFilteredOrders();

  if (loading) {
    return (
      <div className="transactions-loading">
        <div className="spinner"></div>
        <p>Loading transaction history...</p>
      </div>
    );
  }

  return (
    <div className="transactions-container">
      <div className="transactions-header">
        <h1>Transaction History</h1>
        <p className="welcome-message">View all your buy and sell orders</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <span className="stat-label">Total Buy Orders</span>
            <span className="stat-value">{formatTokenAmount(stats.totalBuy)} tokens</span>
            <span className="stat-sub">{formatCurrency(stats.totalSpent)} spent</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📉</div>
          <div className="stat-content">
            <span className="stat-label">Total Sell Orders</span>
            <span className="stat-value">{formatTokenAmount(stats.totalSell)} tokens</span>
            <span className="stat-sub">{formatCurrency(stats.totalReceived)} received</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💵</div>
          <div className="stat-content">
            <span className="stat-label">Net Flow</span>
            <span className={`stat-value ${stats.totalReceived - stats.totalSpent >= 0 ? 'profit' : 'loss'}`}>
              {formatCurrency(stats.totalReceived - stats.totalSpent)}
            </span>
            <span className="stat-sub">Received - Spent</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <span className="stat-label">Total Orders</span>
            <span className="stat-value">{orders.length}</span>
            <span className="stat-sub">All transactions</span>
          </div>
        </div>
      </div>

      <div className="filters-section">
        <div className="filter-group">
          <label>Order Type:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Orders</option>
            <option value="buy">Buy Orders</option>
            <option value="sell">Sell Orders</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Token:</label>
          <select value={tokenFilter} onChange={(e) => setTokenFilter(e.target.value)}>
            <option value="all">All Tokens</option>
            {tokens.map(token => (
              <option key={token.id} value={token.id}>{token.token_symbol}</option>
            ))}
          </select>
        </div>

        <button className="refresh-btn" onClick={fetchOrders}>
          🔄 Refresh
        </button>
      </div>

      <div className="transactions-section">
        {filteredOrders.length === 0 ? (
          <div className="empty-state">
            <p>No transactions found with the selected filters.</p>
            <button className="clear-filters-btn" onClick={() => {
              setFilter('all');
              setTokenFilter('all');
            }}>
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Token</th>
                  <th>Amount</th>
                  <th>Price</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => (
                  <tr key={order.id}>
                    <td>{formatDate(order.created_at)}</td>
                    <td>
                      <span className={`order-type ${order.order_type}`}>
                        {order.order_type?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </td>
                    <td>
                      <span className="token-badge">{getTokenSymbol(order.token)}</span>
                    </td>
                    <td>{formatTokenAmount(order.amount)}</td>
                    <td>{formatCurrency(order.price)}</td>
                    <td>{formatCurrency(order.total)}</td>
                    <td>
                      <span className="status-badge completed">
                        Completed
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="summary-section">
        <h3>Transaction Summary</h3>
        <div className="summary-details">
          <div className="summary-row">
            <span>Total Spent on Buys:</span>
            <span className="spent">{formatCurrency(stats.totalSpent)}</span>
          </div>
          <div className="summary-row">
            <span>Total Received from Sells:</span>
            <span className="received">{formatCurrency(stats.totalReceived)}</span>
          </div>
          <div className="summary-row total">
            <span>Net Investment:</span>
            <span className={stats.totalSpent - stats.totalReceived >= 0 ? 'invested' : 'profit'}>
              {formatCurrency(stats.totalSpent - stats.totalReceived)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Transactions;
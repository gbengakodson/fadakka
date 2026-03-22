import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Portfolio.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

function Portfolio() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [holdings, setHoldings] = useState([]);
  const [grandBalance, setGrandBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [totalValue, setTotalValue] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);
  const [timeframe, setTimeframe] = useState('24h');

  // Coin ID mapping for correct navigation - UPDATED
  const coinIdMap = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'ADA': 'cardano',
    'XRP': 'ripple',
    'LINK': 'chainlink',
    'SUI': 'sui',
    'PEPE': 'pepe',
    'SOL': 'solana',
    'AVAX': 'avalanche-2',
    'DOT': 'polkadot',
    'MATIC': 'matic-network',
    'DOGE': 'dogecoin',
    'UNI': 'uniswap',
    'AAVE': 'aave',
    'LTC': 'litecoin',
    'NEAR': 'near',
    'APT': 'aptos',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'INJ': 'injective-protocol',
    'RNDR': 'render-token',
    'GRT': 'the-graph',
    'FIL': 'filecoin',
    'STX': 'stacks',
    'IMX': 'immutable-x',
    'THETA': 'theta-token',
    'FET': 'fetch-ai',
    'GALA': 'gala',
    'SAND': 'the-sandbox',
    'BNB': 'binancecoin',  // ← ADD THIS LINE
    'TRX': 'tron',
    'XLM': 'stellar',
    'TON': 'toncoin',
    'ALGO': 'algorand'
  };

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
    fetchPortfolioData();
  }, [isAuthenticated, navigate]);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);

      // Fetch GrandBalance
      const balanceResponse = await axios.get(`${API_URL}/wallet/grand-balance/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setGrandBalance(Number(balanceResponse.data.balance_usdc) || 0);

      // Fetch token holdings
      const tokensResponse = await axios.get(`${API_URL}/volatility/user-tokens/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      console.log('Raw holdings:', tokensResponse.data);

      if (!tokensResponse.data || tokensResponse.data.length === 0) {
        setHoldings([]);
        setTotalValue(0);
        setTotalProfit(0);
        setLoading(false);
        return;
      }

      // Process holdings with coin_id for navigation
      const holdingsWithDetails = tokensResponse.data.map((holding) => {
        // Extract base symbol from token_symbol (e.g., "BNB-VT" -> "BNB")
        const baseSymbol = holding.token_symbol?.replace('-VT', '');
        console.log('Base symbol:', baseSymbol);

        // Get the coin_id from mapping
        const coinId = coinIdMap[baseSymbol] || baseSymbol?.toLowerCase() || '';
        console.log('Mapped coinId:', coinId);

        const balance = Number(holding.balance) || 0;
        const currentPrice = Number(holding.current_price) || 0;
        const purchasePrice = Number(holding.purchase_price) || 0;
        const currentValue = Number(holding.current_value) || 0;
        const profitLoss = Number(holding.profit_loss) || 0;
        const profitLossPercentage = Number(holding.profit_loss_percentage) || 0;
        const tokenSymbol = holding.token_symbol || 'Unknown';
        const tokenName = holding.token_name || '';

        return {
          id: holding.id,
          balance: balance,
          currentValue: currentValue,
          averageBuyPrice: purchasePrice,
          profitLoss: profitLoss,
          profitLossPercentage: profitLossPercentage,
          coinId: coinId,  // This is what gets passed to navigate
          token: {
            token_symbol: tokenSymbol,
            name: tokenName,
            current_price: currentPrice,
            coin_id: coinId
          }
        };
      });

      console.log('Processed holdings:', holdingsWithDetails);
      setHoldings(holdingsWithDetails);

      // Calculate totals
      const total = holdingsWithDetails.reduce((sum, h) => sum + h.currentValue, 0);
      const profit = holdingsWithDetails.reduce((sum, h) => sum + h.profitLoss, 0);

      setTotalValue(total);
      setTotalProfit(profit);

    } catch (error) {
      console.error('Error fetching portfolio:', error);
    } finally {
      setLoading(false);
    }
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

  if (loading) {
    return (
      <div className="portfolio-loading">
        <div className="spinner"></div>
        <p>Loading your portfolio...</p>
      </div>
    );
  }

  return (
    <div className="portfolio-container">
      {/* Header */}
      <div className="portfolio-header">
        <h1>My Portfolio</h1>
        <p className="welcome-message">Welcome back, {user?.username}!</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="summary-card">
          <div className="summary-icon">💰</div>
          <div className="summary-content">
            <span className="summary-label">GrandBalance</span>
            <span className="summary-value">{formatCurrency(grandBalance)}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📊</div>
          <div className="summary-content">
            <span className="summary-label">Portfolio Value</span>
            <span className="summary-value">{formatCurrency(totalValue)}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">💵</div>
          <div className="summary-content">
            <span className="summary-label">Total Assets</span>
            <span className="summary-value">{formatCurrency(grandBalance + totalValue)}</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📈</div>
          <div className="summary-content">
            <span className="summary-label">Total P/L</span>
            <span className={`summary-value ${totalProfit >= 0 ? 'profit' : 'loss'}`}>
              {totalProfit >= 0 ? '+' : ''}{formatCurrency(totalProfit)}
            </span>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="holdings-section">
        <div className="section-header">
          <h2>Your Volatility Tokens</h2>
          <div className="timeframe-selector">
            <button
              className={timeframe === '24h' ? 'active' : ''}
              onClick={() => setTimeframe('24h')}
            >
              24h
            </button>
            <button
              className={timeframe === '7d' ? 'active' : ''}
              onClick={() => setTimeframe('7d')}
            >
              7d
            </button>
            <button
              className={timeframe === '30d' ? 'active' : ''}
              onClick={() => setTimeframe('30d')}
            >
              30d
            </button>
          </div>
        </div>

        {holdings.length === 0 ? (
          <div className="empty-state">
            <p>You don't own any volatility tokens yet.</p>
            <button className="browse-btn" onClick={() => navigate('/')}>
              Browse Coins to Trade
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="holdings-table">
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Balance</th>
                  <th>Current Price</th>
                  <th>Avg. Buy Price</th>
                  <th>Current Value</th>
                  <th>P&L</th>
                  <th>P&L %</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => (
                  <tr key={holding.id}>
                    <td className="token-cell">
                      <div className="token-info">
                        <span className="token-symbol">{holding.token.token_symbol}</span>
                        <span className="token-name">{holding.token.name}</span>
                      </div>
                    </td>
                    <td>{formatTokenAmount(holding.balance)}</td>
                    <td>{formatCurrency(holding.token.current_price)}</td>
                    <td>{formatCurrency(holding.averageBuyPrice)}</td>
                    <td>{formatCurrency(holding.currentValue)}</td>
                    <td className={holding.profitLoss >= 0 ? 'profit' : 'loss'}>
                      {holding.profitLoss >= 0 ? '+' : ''}{formatCurrency(holding.profitLoss)}
                    </td>
                    <td className={holding.profitLossPercentage >= 0 ? 'profit' : 'loss'}>
                      {holding.profitLossPercentage >= 0 ? '+' : ''}{holding.profitLossPercentage.toFixed(2)}%
                    </td>
                    <td>
                      <button
                        className="trade-btn"
                        onClick={() => navigate(`/trade/${holding.coinId}`)}
                      >
                        Trade
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Performance Chart */}
      <div className="performance-section">
        <h2>Portfolio Performance</h2>
        <div className="performance-chart">
          <div className="chart-placeholder">
            <p>Performance chart coming soon...</p>
            <p className="placeholder-note">(Will show your portfolio value over time)</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Portfolio;
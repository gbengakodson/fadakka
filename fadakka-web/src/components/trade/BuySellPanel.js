import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import './BuySellPanel.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

function BuySellPanel({ coinId, coinSymbol, currentPrice, orderType, volatilityToken, grandBalance, holdings, onTradeComplete }) {
  const { user } = useAuth();
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState(currentPrice);
  const [stopPrice, setStopPrice] = useState(currentPrice * 0.95);
  const [limitPrice, setLimitPrice] = useState(currentPrice);
  const [localBalance, setLocalBalance] = useState(grandBalance || 0);
  const [localTokenBalance, setLocalTokenBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Update local balance when prop changes
  useEffect(() => {
    setLocalBalance(grandBalance || 0);
  }, [grandBalance]);

  // Update local token balance when holdings change
  useEffect(() => {
    if (holdings) {
      setLocalTokenBalance(Number(holdings.balance) || 0);
    }
  }, [holdings]);

  // Fallback fetch if props aren't provided
  const fetchBalances = async () => {
    try {
      const balanceResponse = await axios.get(`${API_URL}/wallet/grand-balance/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLocalBalance(Number(balanceResponse.data.balance_usdc) || 0);

      const tokenResponse = await axios.get(`${API_URL}/volatility/user-tokens/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const token = tokenResponse.data.find(t => t.token?.coin_id === coinId);
      if (token) {
        setLocalTokenBalance(Number(token.balance) || 0);
      }
    } catch (error) {
      console.error('Error fetching balances:', error);
    }
  };

  const handleBuy = async () => {
    if (!amount) {
      setMessage({ type: 'error', text: 'Please enter an amount' });
      return;
    }

    const numAmount = Number(amount);
    const total = numAmount * Number(price);

    if (total > localBalance) {
      setMessage({ type: 'error', text: `Insufficient GrandBalance. Need $${total.toFixed(2)}` });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Get token ID
      const tokenResponse = await axios.get(`${API_URL}/volatility/tokens/`);
      const token = tokenResponse.data.find(t => t.coin_id === coinId);

      if (!token) {
        throw new Error('Token not found');
      }

      const response = await axios.post(`${API_URL}/volatility/buy/`, {
        token_id: token.id,
        amount: numAmount,
        price: Number(price)
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `✅ Successfully bought ${amount} ${volatilityToken}`
        });
        setAmount('');
        // Refresh balances
        if (onTradeComplete) {
          onTradeComplete();
        } else {
          fetchBalances();
        }
      }
    } catch (error) {
      console.error('Buy error:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.error || 'Transaction failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSell = async () => {
    if (!amount) {
      setMessage({ type: 'error', text: 'Please enter an amount' });
      return;
    }

    const numAmount = Number(amount);

    if (numAmount > localTokenBalance) {
      setMessage({ type: 'error', text: `Insufficient token balance. You have ${localTokenBalance.toFixed(8)} ${coinSymbol}` });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const tokenResponse = await axios.get(`${API_URL}/volatility/tokens/`);
      const token = tokenResponse.data.find(t => t.coin_id === coinId);

      if (!token) {
        throw new Error('Token not found');
      }

      const response = await axios.post(`${API_URL}/volatility/sell/`, {
        token_id: token.id,
        amount: numAmount,
        price: Number(price)
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `✅ Successfully sold ${amount} ${volatilityToken}`
        });
        setAmount('');
        // Refresh balances
        if (onTradeComplete) {
          onTradeComplete();
        } else {
          fetchBalances();
        }
      }
    } catch (error) {
      console.error('Sell error:', error);
      setMessage({
        type: 'error',
        text: error.response?.data?.error || 'Transaction failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = () => {
    if (!amount) return '0.00';
    return (Number(amount) * Number(price)).toFixed(2);
  };

  const calculateNodeFee = () => {
    if (!amount) return '0.00';
    const total = Number(amount) * Number(price);
    return (total * 0.1).toFixed(2);
  };

  const calculateNetReceive = () => {
    if (!amount) return '0.00';
    const total = Number(amount) * Number(price);
    return (total * 0.9).toFixed(2);
  };

  return (
    <div className="buy-sell-panel">
      {/* Balance Display */}
      <div className="balance-section">
        <div className="balance-info">
          <span className="balance-label">💰 GrandBalance:</span>
          <span className="balance-amount">${localBalance.toFixed(2)} USDC</span>
        </div>
        <div className="balance-info">
          <span className="balance-label">📊 Your {coinSymbol} Balance:</span>
          <span className="token-balance">{localTokenBalance.toFixed(8)} {coinSymbol}</span>
        </div>
      </div>

      {/* Token Info */}
      <div className="token-info">
        <strong>{volatilityToken}</strong>
        <span className="token-price">${Number(price).toFixed(2)}</span>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* Order Type Inputs */}
      {orderType === 'limit' && (
        <div className="input-group">
          <label>Limit Price ($)</label>
          <input
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            step="0.01"
            min="0.01"
          />
        </div>
      )}

      {orderType === 'stop' && (
        <>
          <div className="input-group">
            <label>Stop Price ($)</label>
            <input
              type="number"
              value={stopPrice}
              onChange={(e) => setStopPrice(e.target.value)}
              step="0.01"
              min="0.01"
            />
          </div>
          <div className="input-group">
            <label>Limit Price ($)</label>
            <input
              type="number"
              value={limitPrice}
              onChange={(e) => setLimitPrice(e.target.value)}
              step="0.01"
              min="0.01"
            />
          </div>
        </>
      )}

      {/* Amount Input */}
      <div className="input-group">
        <label>Amount</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          step="0.001"
          min="0.001"
        />
        <span className="unit">{coinSymbol}</span>
      </div>

      {/* Order Summary */}
      <div className="order-summary">
        <div className="summary-row">
          <span>Total:</span>
          <span className="total-amount">${calculateTotal()}</span>
        </div>
        <div className="summary-row">
          <span>Node Fee (10%):</span>
          <span className="fee-amount">${calculateNodeFee()}</span>
        </div>
        <div className="summary-row highlight">
          <span>You will receive:</span>
          <span className="net-amount">${calculateNetReceive()} USDC</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="button-group">
        <button
          className="buy-btn"
          onClick={handleBuy}
          disabled={loading}
        >
          {loading ? 'Processing...' : `Buy ${volatilityToken}`}
        </button>
        <button
          className="sell-btn"
          onClick={handleSell}
          disabled={loading || localTokenBalance === 0}
        >
          {loading ? 'Processing...' : `Sell ${volatilityToken}`}
        </button>
      </div>
    </div>
  );
}

export default BuySellPanel;
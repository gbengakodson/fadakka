import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './GrandBalanceCard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const GrandBalanceCard = ({ balance, onRefresh, currentCoinId, onSelectCoin }) => {
  const [showDeposit, setShowDeposit] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [localBalance, setLocalBalance] = useState(balance || 0);
  const [quickCoins, setQuickCoins] = useState([]);
  const [coinsLoading, setCoinsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    setLocalBalance(balance || 0);
  }, [balance]);

  useEffect(() => {
    fetchQuickCoins();
  }, []);

  const fetchQuickCoins = async () => {
    try {
      const response = await fetch(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=12&page=1&sparkline=false'
      );
      const data = await response.json();
      setQuickCoins(data);
    } catch (error) {
      console.error('Error fetching quick coins:', error);
    } finally {
      setCoinsLoading(false);
    }
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/wallet/grand-balance/`,
        {
          action: 'deposit',
          amount: depositAmount
        },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }
      );

      if (response.data.success) {
        setLocalBalance(response.data.new_balance);
        if (onRefresh) onRefresh();
        setShowDeposit(false);
        setDepositAmount('');
        alert(`✅ Deposited $${depositAmount} USDC successfully!`);
      }
    } catch (error) {
      console.error('Deposit error:', error);
      alert('Deposit failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCoinSelect = (coinId) => {
    if (onSelectCoin) {
      onSelectCoin(coinId);
    } else {
      navigate(`/trade/${coinId}`);
    }
  };

  return (
    <div className="grand-balance-card">
      {/* Balance Section */}
      <div className="balance-section">
        <div className="card-header">
          <h3>💰 GrandBalance</h3>
          <button className="refresh-btn" onClick={onRefresh} title="Refresh balance">
            ⟳
          </button>
        </div>

        <div className="balance-amount">
          ${localBalance?.toFixed(2) || '0.00'} USDC
        </div>

        <div className="card-actions">
          <button
            className="deposit-btn"
            onClick={() => setShowDeposit(!showDeposit)}
          >
            {showDeposit ? 'Cancel' : '+ Deposit'}
          </button>
        </div>

        {showDeposit && (
          <form onSubmit={handleDeposit} className="deposit-form">
            <input
              type="number"
              value={depositAmount}
              onChange={(e) => setDepositAmount(e.target.value)}
              placeholder="Amount (USDC)"
              min="1"
              step="1"
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Confirm Deposit'}
            </button>
          </form>
        )}
      </div>

      {/* Divider */}
      <div className="card-divider"></div>

      {/* Quick Coins Section */}
      <div className="quick-coins-section">
        <h4>⚡ Quick Trade</h4>
        {coinsLoading ? (
          <div className="quick-coins-loading">Loading coins...</div>
        ) : (
          <div className="coin-grid">
            {quickCoins.map((coin) => (
              <button
                key={coin.id}
                className={`coin-tile ${currentCoinId === coin.id ? 'active' : ''}`}
                onClick={() => handleCoinSelect(coin.id)}
                title={coin.name}
              >
                <img src={coin.image} alt={coin.name} className="coin-tile-icon" />
                <span className="coin-tile-symbol">{coin.symbol.toUpperCase()}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GrandBalanceCard;
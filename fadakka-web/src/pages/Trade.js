import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import TradingChart from '../components/trade/TradingChart';
import BuySellPanel from '../components/trade/BuySellPanel';
import OrderBook from '../components/trade/OrderBook';
import GrandBalanceCard from '../components/trade/GrandBalanceCard';
import './Trade.css';

function Trade() {
  const { coinId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [coinData, setCoinData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState('spot');
  const [orderType, setOrderType] = useState('limit');
  const [grandBalance, setGrandBalance] = useState(0);
  const [holdings, setHoldings] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
    fetchCoinData();
    fetchGrandBalance();
    fetchUserHoldings();
  }, [coinId, isAuthenticated, navigate, retryCount]);

  const fetchCoinData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use a proxy to avoid CORS issues, or fetch from your backend
      const url = `https://api.coingecko.com/api/v3/coins/${coinId}?localization=false&tickers=true&market_data=true&community_data=false&developer_data=false`;

      console.log('Fetching from URL:', url);

      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
        },
        // Add a timeout
        signal: AbortSignal.timeout(10000)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Coin data received:', data);
      setCoinData(data);

    } catch (error) {
      console.error('Error fetching coin data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchGrandBalance = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/wallet/grand-balance/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setGrandBalance(data.balance_usdc || 0);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const fetchUserHoldings = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/volatility/user-tokens/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      // Find holding for this specific token
      const tokenHolding = data.find(h =>
        h.token_symbol === `${coinId?.toUpperCase()}-VT` ||
        h.token?.coin_id === coinId
      );
      setHoldings(tokenHolding);
    } catch (error) {
      console.error('Error fetching holdings:', error);
    }
  };

  const refreshBalance = () => {
    fetchGrandBalance();
    fetchUserHoldings();
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading trading page...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Network Error</h2>
        <p>Could not fetch live prices: {error}</p>
        <button onClick={handleRetry} className="retry-btn">
          Retry
        </button>
        <button onClick={() => navigate('/')} className="back-btn">
          Back to Coins
        </button>
      </div>
    );
  }

  if (!coinData) {
    return (
      <div className="error-container">
        <h2>Coin not found</h2>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    );
  }

  // Safe check for symbol - add fallback
  const coinSymbol = coinData?.symbol?.toUpperCase() || coinId?.toUpperCase() || 'BTC';
  const volatilityToken = `${coinSymbol}-VT`;
  const currentPrice = coinData?.market_data?.current_price?.usd || 0;

  return (
    <div className="trade-container">
      {/* Top Navigation */}
      <div className="trade-nav">
        <div className="nav-left">
          <button className="back-btn" onClick={() => navigate('/')}>
            ← Back to Coins
          </button>
          <div className="coin-info">
            {coinData?.image?.small && (
              <img src={coinData.image.small} alt={coinData.name} className="coin-icon" />
            )}
            <div>
              <h1>{coinData?.name || 'Unknown'} <span className="coin-symbol">{coinSymbol}</span></h1>
              <span className="volatility-badge">Volatility Token: {volatilityToken}</span>
            </div>
          </div>
        </div>
        <div className="price-info">
          <div className="current-price">${currentPrice.toLocaleString()}</div>
          <div className={`price-change ${coinData?.market_data?.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
            {coinData?.market_data?.price_change_percentage_24h?.toFixed(2) || 0}%
          </div>
        </div>
      </div>

      {/* Main Trading Grid */}
      <div className="trading-grid">
        {/* Left Column - Chart */}
        <div className="chart-section">
          <div className="chart-tabs">
            <button className={selectedTab === 'spot' ? 'active' : ''} onClick={() => setSelectedTab('spot')}>Spot</button>
            <button className={selectedTab === 'margin' ? 'active' : ''} onClick={() => setSelectedTab('margin')}>Margin</button>
            <button className={selectedTab === 'futures' ? 'active' : ''} onClick={() => setSelectedTab('futures')}>Futures</button>
          </div>

          <TradingChart coinId={coinId} />
        </div>

        {/* Right Column - Order Book */}
        <OrderBook coinId={coinId} currentPrice={currentPrice} />

        {/* Bottom Left - Buy/Sell Panel */}
        <div className="order-panel">
          <div className="order-tabs">
            <button className={orderType === 'limit' ? 'active' : ''} onClick={() => setOrderType('limit')}>Limit</button>
            <button className={orderType === 'market' ? 'active' : ''} onClick={() => setOrderType('market')}>Market</button>
            <button className={orderType === 'stop' ? 'active' : ''} onClick={() => setOrderType('stop')}>Stop-Limit</button>
          </div>

          <BuySellPanel
            coinId={coinId}
            coinSymbol={coinSymbol}
            currentPrice={currentPrice}
            orderType={orderType}
            volatilityToken={volatilityToken}
            grandBalance={grandBalance}
            holdings={holdings}
            onTradeComplete={refreshBalance}
          />
        </div>

        {/* Bottom Right - GrandBalance */}
           <GrandBalanceCard
                balance={grandBalance}
                onRefresh={refreshBalance}
                currentCoinId={coinId}
                onSelectCoin={(newCoinId) => navigate(`/trade/${newCoinId}`)}
           />



      </div>
    </div>
  );
}

export default Trade;
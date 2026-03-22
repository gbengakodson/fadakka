import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './CoinList.css';

// Your 20 selected cryptocurrencies
const MY_COINS = [
  'bitcoin', 'ethereum', 'ripple', 'binancecoin', 'solana',
  'tron', 'dogecoin', 'cardano', 'chainlink', 'stellar',
  'sui', 'toncoin', 'shiba-inu', 'polkadot', 'aave',
  'near', 'pepe', 'render-token', 'algorand', 'filecoin'
];

function CoinList() {
  const [coins, setCoins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const fetchLivePrices = async () => {
    try {
      setLoading(true);
      console.log('Fetching live prices for your 20 coins...');

      const ids = MY_COINS.join(',');
      const response = await fetch(
        `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${ids}&order=market_cap_desc&per_page=20&page=1&sparkline=false&price_change_percentage=24h`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Sort coins according to your original list order
      const sortedCoins = MY_COINS.map(id =>
        data.find(coin => coin.id === id)
      ).filter(coin => coin !== undefined);

      setCoins(sortedCoins);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching live prices:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLivePrices();
    const interval = setInterval(fetchLivePrices, 60000);
    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price) => {
    if (!price) return '$0.00';
    if (price < 0.01) return `$${price.toFixed(6)}`;
    if (price < 1) return `$${price.toFixed(4)}`;
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatMarketCap = (cap) => {
    if (!cap) return '$0';
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`;
    return `$${cap.toLocaleString()}`;
  };

  const filteredCoins = coins.filter(coin =>
    coin?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    coin?.symbol?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCoinClick = (coinId) => {
    navigate(`/trade/${coinId}`);
  };

  if (loading && coins.length === 0) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading cryptocurrencies...</p>
      </div>
    );
  }

  if (error && coins.length === 0) {
    return (
      <div className="error-container">
        <h3>Network Error</h3>
        <p>Could not fetch live prices: {error}</p>
        <button onClick={fetchLivePrices} className="refresh-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="home-container">
      <div className="home-header">
        <h1>Node</h1>
        <p className="home-subtitle">...market volatility to your advantage</p>
        {lastUpdate && (
          <p className="update-time">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}

        <div className="search-container">
          <input
            type="text"
            placeholder="Search coins..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <div className="coins-grid">
        {filteredCoins.map((coin, index) => coin && (
          <div
            key={coin.id}
            className="coin-card clickable"
            onClick={() => handleCoinClick(coin.id)}
          >
            <div className="coin-rank">{index + 1}</div>
            <div className="coin-header">
              <img src={coin.image} alt={coin.name} className="coin-image" />
              <div className="coin-title">
                <h3 className="coin-symbol">{coin.symbol.toUpperCase()}</h3>
                <span className="coin-name">{coin.name}</span>
              </div>
            </div>

            <div className="coin-price-section">
              <div className="coin-price">
                {formatPrice(coin.current_price)}
              </div>
              <div className={`coin-change ${coin.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
                {coin.price_change_percentage_24h?.toFixed(2)}%
              </div>
            </div>

            <div className="coin-details">
              <div className="coin-detail-row">
                <span>Market Cap</span>
                <span className="detail-value">{formatMarketCap(coin.market_cap)}</span>
              </div>
              <div className="coin-detail-row">
                <span>Volume (24h)</span>
                <span className="detail-value">{formatMarketCap(coin.total_volume)}</span>
              </div>
            </div>

            <div className="coin-footer">
              <span className="volatility-badge">
                {coin.symbol.toUpperCase()}-VT
              </span>
              <span className="trade-indicator">Trade →</span>
            </div>
          </div>
        ))}
      </div>

      {filteredCoins.length === 0 && (
        <div className="empty-state">
          <p>No coins found matching "{searchTerm}"</p>
        </div>
      )}

      <div className="refresh-container">
        <button onClick={fetchLivePrices} className="refresh-btn">
          Refresh Prices
        </button>
      </div>
    </div>
  );
}

export default CoinList;
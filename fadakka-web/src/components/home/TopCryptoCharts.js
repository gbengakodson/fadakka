import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './TopCryptoCharts.css';

const API_URL = 'https://api.coingecko.com/api/v3';

const TopCryptoCharts = () => {
  const [coins, setCoins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('7d');

  useEffect(() => {
    fetchTopCoins();
  }, [timeframe]);

  const fetchTopCoins = async () => {
    try {
      // Fetch top 3 coins by market cap
      const response = await fetch(
        `${API_URL}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=3&page=1&sparkline=true`
      );
      const data = await response.json();

      // Fetch historical data for charts
      const coinsWithHistory = await Promise.all(
        data.map(async (coin) => {
          const historyRes = await fetch(
            `${API_URL}/coins/${coin.id}/market_chart?vs_currency=usd&days=${timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 1}`
          );
          const history = await historyRes.json();
          return {
            ...coin,
            chartData: history.prices.map(([timestamp, price]) => ({
              time: new Date(timestamp).toLocaleDateString(),
              price: price
            }))
          };
        })
      );

      setCoins(coinsWithHistory);
    } catch (error) {
      console.error('Error fetching top coins:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="top-charts-loading">Loading market data...</div>;
  }

  return (
    <div className="top-crypto-charts">
      <div className="charts-header">
        <h2>Top Cryptocurrencies</h2>
        <div className="timeframe-selector">
          <button className={timeframe === '1d' ? 'active' : ''} onClick={() => setTimeframe('1d')}>
            24h
          </button>
          <button className={timeframe === '7d' ? 'active' : ''} onClick={() => setTimeframe('7d')}>
            7d
          </button>
          <button className={timeframe === '30d' ? 'active' : ''} onClick={() => setTimeframe('30d')}>
            30d
          </button>
        </div>
      </div>

      <div className="charts-grid">
        {coins.map((coin) => (
          <div key={coin.id} className="chart-card">
            <div className="chart-card-header">
              <div className="coin-info">
                <img src={coin.image} alt={coin.name} className="coin-icon" />
                <div>
                  <div className="coin-name">{coin.name}</div>
                  <div className="coin-symbol">{coin.symbol.toUpperCase()}</div>
                </div>
              </div>
              <div className="coin-price">
                ${coin.current_price.toLocaleString()}
                <span className={`price-change ${coin.price_change_percentage_24h >= 0 ? 'positive' : 'negative'}`}>
                  {coin.price_change_percentage_24h?.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={150}>
                <LineChart data={coin.chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" hide />
                  <YAxis domain={['auto', 'auto']} hide />
                  <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke={coin.price_change_percentage_24h >= 0 ? '#10b981' : '#ef4444'}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopCryptoCharts;
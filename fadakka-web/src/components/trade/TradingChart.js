import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './TradingChart.css';

function TradingChart({ coinId }) {
  const [priceData, setPriceData] = useState([]);
  const [timeframe, setTimeframe] = useState('1d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPriceData();
  }, [coinId, timeframe]);

  const fetchPriceData = async () => {
    setLoading(true);
    try {
      let days = 30;
      switch(timeframe) {
        case '1h': days = 1; break;
        case '4h': days = 7; break;
        case '1d': days = 30; break;
        case '1w': days = 90; break;
        case '1m': days = 365; break;
        default: days = 30;
      }

      const response = await fetch(
        `https://api.coingecko.com/api/v3/coins/${coinId}/market_chart?vs_currency=usd&days=${days}`
      );

      if (!response.ok) throw new Error('Failed to fetch data');

      const data = await response.json();

      // Format data for line chart
      const formattedData = data.prices.map(([timestamp, price]) => ({
        time: new Date(timestamp).toLocaleDateString(),
        price: price,
        fullTime: new Date(timestamp).toLocaleString()
      }));

      setPriceData(formattedData);
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-time">{payload[0].payload.fullTime}</p>
          <p className="tooltip-price">${payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="chart-loading">
        <div className="spinner-small"></div>
        <p>Loading chart data...</p>
      </div>
    );
  }

  return (
    <div className="trading-chart-wrapper">
      <div className="chart-controls">
        <div className="timeframe-buttons">
          <button
            className={timeframe === '1h' ? 'active' : ''}
            onClick={() => setTimeframe('1h')}
          >
            1H
          </button>
          <button
            className={timeframe === '4h' ? 'active' : ''}
            onClick={() => setTimeframe('4h')}
          >
            4H
          </button>
          <button
            className={timeframe === '1d' ? 'active' : ''}
            onClick={() => setTimeframe('1d')}
          >
            1D
          </button>
          <button
            className={timeframe === '1w' ? 'active' : ''}
            onClick={() => setTimeframe('1w')}
          >
            1W
          </button>
          <button
            className={timeframe === '1m' ? 'active' : ''}
            onClick={() => setTimeframe('1m')}
          >
            1M
          </button>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={priceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TradingChart;
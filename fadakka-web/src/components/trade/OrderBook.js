import React, { useState, useEffect } from 'react';
import './OrderBook.css';

function OrderBook({ coinId, currentPrice }) {
  const [bids, setBids] = useState([]);
  const [asks, setAsks] = useState([]);

  useEffect(() => {
    // Simulate order book data
    generateOrderBook();
    const interval = setInterval(generateOrderBook, 5000);
    return () => clearInterval(interval);
  }, [currentPrice]);

  const generateOrderBook = () => {
    // Generate fake bids (buy orders)
    const newBids = [];
    for (let i = 0; i < 8; i++) {
      const price = currentPrice * (1 - (i + 1) * 0.001);
      const amount = Math.random() * 10 + 1;
      const total = price * amount;
      newBids.push({
        price: price.toFixed(2),
        amount: amount.toFixed(4),
        total: total.toFixed(2)
      });
    }

    // Generate fake asks (sell orders)
    const newAsks = [];
    for (let i = 0; i < 8; i++) {
      const price = currentPrice * (1 + (i + 1) * 0.001);
      const amount = Math.random() * 10 + 1;
      const total = price * amount;
      newAsks.push({
        price: price.toFixed(2),
        amount: amount.toFixed(4),
        total: total.toFixed(2)
      });
    }

    setBids(newBids.sort((a, b) => parseFloat(b.price) - parseFloat(a.price)));
    setAsks(newAsks.sort((a, b) => parseFloat(a.price) - parseFloat(b.price)));
  };

  return (
    <div className="order-book">
      <h3>Order Book</h3>

      <div className="order-book-header">
        <span>Price (USDT)</span>
        <span>Amount</span>
        <span>Total</span>
      </div>

      <div className="asks">
        {asks.map((ask, i) => (
          <div key={i} className="order-row ask">
            <span className="price">{ask.price}</span>
            <span>{ask.amount}</span>
            <span>{ask.total}</span>
          </div>
        ))}
      </div>

      <div className="current-price-row">
        <span className="current-price">{currentPrice.toFixed(2)}</span>
      </div>

      <div className="bids">
        {bids.map((bid, i) => (
          <div key={i} className="order-row bid">
            <span className="price">{bid.price}</span>
            <span>{bid.amount}</span>
            <span>{bid.total}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OrderBook;
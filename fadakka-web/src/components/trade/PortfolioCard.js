import React from 'react';
import './PortfolioCard.css';

const PortfolioCard = ({ holding, onSell, onSetAlert }) => {
  const profitClass = holding.profit_loss >= 0 ? 'positive' : 'negative';
  const sellDisabled = !holding.can_sell;

  return (
    <div className="portfolio-card">
      <div className="card-header">
        <h3>{holding.token}</h3>
        <span className={`profit-badge ${profitClass}`}>
          {holding.profit_loss_percentage > 0 ? '+' : ''}{holding.profit_loss_percentage}%
        </span>
      </div>

      <div className="card-details">
        <div className="detail-row">
          <span>Balance:</span>
          <span className="amount">{holding.balance.toFixed(8)}</span>
        </div>
        <div className="detail-row">
          <span>Purchase Price:</span>
          <span>${holding.purchase_price.toFixed(2)}</span>
        </div>
        <div className="detail-row">
          <span>Current Price:</span>
          <span>${holding.current_price.toFixed(2)}</span>
        </div>
        <div className="detail-row">
          <span>Current Value:</span>
          <span>${holding.current_value.toFixed(2)}</span>
        </div>
        <div className="detail-row profit-row">
          <span>Profit/Loss:</span>
          <span className={profitClass}>
            {holding.profit_loss >= 0 ? '+' : ''}{holding.profit_loss.toFixed(2)} USD
          </span>
        </div>
        <div className="detail-row">
          <span>Yield Earned:</span>
          <span className="yield">${holding.yield_earned.toFixed(2)}</span>
        </div>
      </div>

      <div className="card-actions">
        <button
          onClick={() => onSell(holding)}
          disabled={sellDisabled}
          className={sellDisabled ? 'disabled' : 'sell-btn'}
        >
          {sellDisabled ? 'Locked (Price Lower)' : 'Sell Now'}
        </button>
        <button
          onClick={() => onSetAlert(holding)}
          className="alert-btn"
        >
          Set Price Alert
        </button>
      </div>

      {holding.auto_sell_pending && (
        <div className="auto-sell-badge">
          ⚡ Will auto-sell at 20% gain
        </div>
      )}
    </div>
  );
};

export default PortfolioCard;
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const RecentDistributions = () => {
  const [distributions, setDistributions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDistributions();
  }, []);

  const fetchDistributions = async () => {
    try {
      const response = await axios.get(`${API_URL}/volatility/yield-distributions/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      console.log('Fetched distributions:', response.data);
      setDistributions(response.data);
    } catch (error) {
      console.error('Error fetching distributions:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading distributions...</div>;
  }

  if (distributions.length === 0) {
    return <div className="no-data">No distributions yet</div>;
  }

  return (
    <div className="recent-distributions">
      <h3>Recent Yield Distributions</h3>
      <div className="distributions-list">
        {distributions.map((dist) => (
          <div key={dist.id} className="distribution-item">
            <div className="dist-token">{dist.token}</div>
            <div className="dist-amount">+${dist.amount.toFixed(6)}</div>
            <div className="dist-date">{new Date(dist.date).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentDistributions;
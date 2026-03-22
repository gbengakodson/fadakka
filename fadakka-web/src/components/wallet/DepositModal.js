import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';
import './WalletModals.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

const DepositModal = ({ isOpen, onClose, onSuccess }) => {
  console.log('🔵 DepositModal rendering, isOpen:', isOpen);

  const [loading, setLoading] = useState(false);
  const [depositInfo, setDepositInfo] = useState(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');
  const [faucetLoading, setFaucetLoading] = useState(false);
  const [faucetMessage, setFaucetMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchDepositAddress();
    }
  }, [isOpen]);

  const fetchDepositAddress = async () => {
    console.log('🔵 Fetching deposit address...');
    const token = localStorage.getItem('token');
    console.log('🔵 Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'No token found');

    setLoading(true);
    setError('');

    try {
      const response = await axios.get(`${API_URL}/wallet/usdc/deposit-address/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      console.log('🔵 Deposit address response:', response.data);
      setDepositInfo(response.data);
    } catch (err) {
      console.error('🔵 Deposit address error:', err);
      console.error('🔵 Error response:', err.response?.data);
      console.error('🔵 Error status:', err.response?.status);

      if (err.response?.status === 401) {
        setError('Session expired. Please log in again.');
      } else if (err.response?.status === 404) {
        setError('Deposit endpoint not found. Please contact support.');
      } else if (err.code === 'ERR_NETWORK') {
        setError('Cannot connect to server. Please check if backend is running.');
      } else {
        setError(err.response?.data?.error || 'Failed to get deposit address');
      }
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const requestTestFunds = async () => {
    if (!depositInfo?.address) return;

    setFaucetLoading(true);
    setFaucetMessage('');

    try {
      // Try to request test SOL from multiple faucets
      const response = await axios.post('/api/wallet/request-test-funds/', {
        address: depositInfo.address
      });

      if (response.data.success) {
        setFaucetMessage('✅ Test SOL requested! Please wait a few moments for it to arrive.');
      } else {
        setFaucetMessage(response.data.message || 'Faucet is busy. Try manual options below.');
      }
    } catch (err) {
      setFaucetMessage('Faucet limit reached. Please use the manual options below.');
    } finally {
      setFaucetLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Deposit USDC</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loading-spinner">
              <div className="spinner-small"></div>
              <p>Getting your deposit address...</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              <p>❌ {error}</p>
              <button
                className="btn-secondary"
                onClick={fetchDepositAddress}
                style={{ marginTop: '10px' }}
              >
                Try Again
              </button>
            </div>
          )}

          {depositInfo && !loading && (
            <>
              <div className="info-box">
                <p>🔷 Send only <strong>USDC on Solana network</strong> to this address:</p>
              </div>

              <div className="address-box">
                <div className="address-label">Your Deposit Address</div>
                <div className="address-value">
                  <code>{depositInfo.address}</code>
                  <button
                    className="copy-btn"
                    onClick={() => copyToClipboard(depositInfo.address)}
                    title="Copy address"
                  >
                    {copied ? '✓' : '📋'}
                  </button>
                </div>
              </div>

              {depositInfo.memo && (
                <div className="address-box">
                  <div className="address-label">Memo / Destination Tag</div>
                  <div className="address-value">
                    <code>{depositInfo.memo}</code>
                    <button
                      className="copy-btn"
                      onClick={() => copyToClipboard(depositInfo.memo)}
                      title="Copy memo"
                    >
                      📋
                    </button>
                  </div>
                </div>
              )}

              <div className="qr-section">
                <p>Scan with your Solana wallet:</p>
                <div className="qr-code">
                  <QRCodeSVG
                    value={depositInfo.address}
                    size={200}
                    bgColor="#ffffff"
                    fgColor="#000000"
                    level="L"
                  />
                </div>
              </div>

              {/* Get Test Funds Section */}
              <div className="test-funds-section">
                <h4>🧪 Get Test USDC (Devnet)</h4>
                <p className="test-note">
                  Since you're on testnet, you can get free test USDC from these faucets:
                </p>

                <div className="faucet-buttons">
                  <a
                    href="https://solfaucet.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="faucet-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(depositInfo.address);
                      alert('Address copied! Paste it in the faucet website.');
                    }}
                  >
                    🌊 SolFaucet (SOL)
                  </a>
                  <a
                    href="https://faucet.solana.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="faucet-btn"
                  >
                    🔵 Solana Faucet
                  </a>
                  <a
                    href="https://spl-token-faucet.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="faucet-btn"
                  >
                    💵 USDC Faucet
                  </a>
                </div>

                <div className="manual-instructions">
                  <p><strong>How to get test USDC:</strong></p>
                  <ol>
                    <li>Copy your deposit address above</li>
                    <li>Visit <a href="https://solfaucet.com/" target="_blank">solfaucet.com</a></li>
                    <li>Paste your address and request SOL (you need SOL for gas fees)</li>
                    <li>Then visit a USDC faucet to get test USDC</li>
                    <li>Send USDC to your address above</li>
                  </ol>
                </div>

                {faucetMessage && (
                  <div className={`faucet-message ${faucetMessage.includes('✅') ? 'success' : 'error'}`}>
                    {faucetMessage}
                  </div>
                )}
              </div>

              <div className="instructions">
                <h4>📝 Instructions:</h4>
                <ol>
                  <li>Open your Solana wallet (Phantom, Solflare, etc.)</li>
                  <li>Get test SOL from faucet (for gas fees)</li>
                  <li>Get test USDC from faucet</li>
                  <li>Send USDC to the address above</li>
                  <li>Funds will appear in your GrandBalance after confirmation</li>
                  <li>Minimum deposit: 10 USDC</li>
                  <li>Processing time: 1-2 minutes after network confirmation</li>
                </ol>
              </div>

              <div className="warning-box">
                ⚠️ <strong>Important:</strong> Only send USDC on Solana network.
                Sending on other networks (Ethereum, BSC, etc.) will result in permanent loss.
              </div>

              <div className="info-box">
                <p>💡 <strong>Tip:</strong> You need a small amount of SOL in your wallet for gas fees.
                Get free test SOL from the faucets above first!</p>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Close</button>
          {!depositInfo && !loading && !error && (
            <button
              className="btn-primary"
              onClick={fetchDepositAddress}
            >
              Retry
            </button>
          )}
          {depositInfo && (
            <>
              <button
                className="btn-primary"
                onClick={() => window.open('https://solfaucet.com/', '_blank')}
              >
                Get Test SOL
              </button>
              <button
                className="btn-primary"
                onClick={() => window.open('https://spl-token-faucet.com/', '_blank')}
              >
                Get Test USDC
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default DepositModal;
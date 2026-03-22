import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsOpen(false);
    setShowUserMenu(false);
  }, [location]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target)
      ) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.classList.add('menu-open');
    } else {
      document.body.classList.remove('menu-open');
    }
    return () => document.body.classList.remove('menu-open');
  }, [isOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsOpen(false);
    setShowUserMenu(false);
  };

  const navLinks = [
    { path: '/', label: 'Trade', icon: '📊' },
    { path: '/dashboard', label: 'Dashboard', icon: '📈' },
    { path: '/portfolio', label: 'Portfolio', icon: '💰' },
    { path: '/transactions', label: 'History', icon: '📜' },
    { path: '/yield', label: 'Yield', icon: '🌱' },  // ← Add Yield page link
  ];

  return (
    <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">Fadakka</span>
          <span className="logo-badge">Volatility</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="nav-menu-desktop">
          {isAuthenticated ? (
            <>
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
                >
                  <span className="nav-icon">{link.icon}</span>
                  <span className="nav-label">{link.label}</span>
                </Link>
              ))}
            </>
          ) : (
            <div className="nav-auth">
              <Link to="/login" className="nav-link login-link">
                Login
              </Link>
              <Link to="/register" className="nav-link register-link">
                Sign Up
              </Link>
            </div>
          )}
        </div>

        {/* User Menu (Desktop) */}
        {isAuthenticated && (
          <div className="user-menu-desktop">
            <button
              ref={buttonRef}
              className="user-menu-button"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="user-avatar">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <span className="user-name">{user?.username}</span>
              <span className={`dropdown-arrow ${showUserMenu ? 'open' : ''}`}>▼</span>
            </button>

            {showUserMenu && (
              <div ref={dropdownRef} className="user-dropdown">
                <div className="dropdown-header">
                  <div className="dropdown-user-avatar">
                    {user?.username?.charAt(0).toUpperCase()}
                  </div>
                  <div className="dropdown-user-info">
                    <div className="dropdown-user-name">{user?.username}</div>
                    <div className="dropdown-user-email">{user?.email || 'user@example.com'}</div>
                  </div>
                </div>
                <div className="dropdown-divider"></div>
                <Link to="/profile" className="dropdown-item" onClick={() => setShowUserMenu(false)}>
                  <span className="dropdown-icon">👤</span>
                  Profile
                </Link>
                <Link to="/settings" className="dropdown-item" onClick={() => setShowUserMenu(false)}>
                  <span className="dropdown-icon">⚙️</span>
                  Settings
                </Link>
                <Link to="/yield" className="dropdown-item" onClick={() => setShowUserMenu(false)}>
                  <span className="dropdown-icon">🌱</span>
                  Yield Dashboard
                </Link>
                <div className="dropdown-divider"></div>
                <button onClick={handleLogout} className="dropdown-item logout">
                  <span className="dropdown-icon">🚪</span>
                  Logout
                </button>
              </div>
            )}
          </div>
        )}

        {/* Mobile Menu Button */}
        <button
          className={`mobile-menu-btn ${isOpen ? 'open' : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        {/* Mobile Navigation */}
        <div className={`mobile-menu ${isOpen ? 'open' : ''}`}>
          <div className="mobile-menu-header">
            {isAuthenticated ? (
              <div className="mobile-user-info">
                <div className="mobile-user-avatar">
                  {user?.username?.charAt(0).toUpperCase()}
                </div>
                <div className="mobile-user-details">
                  <div className="mobile-user-name">{user?.username}</div>
                  <div className="mobile-user-email">{user?.email || 'user@example.com'}</div>
                </div>
              </div>
            ) : (
              <div className="mobile-auth-buttons">
                <Link to="/login" className="mobile-login-btn" onClick={() => setIsOpen(false)}>Login</Link>
                <Link to="/register" className="mobile-register-btn" onClick={() => setIsOpen(false)}>Sign Up</Link>
              </div>
            )}
          </div>

          <div className="mobile-menu-links">
            {isAuthenticated ? (
              <>
                {navLinks.map((link) => (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`mobile-link ${location.pathname === link.path ? 'active' : ''}`}
                    onClick={() => setIsOpen(false)}
                  >
                    <span className="mobile-link-icon">{link.icon}</span>
                    <span className="mobile-link-label">{link.label}</span>
                  </Link>
                ))}
                <div className="mobile-divider"></div>
                <Link to="/profile" className="mobile-link" onClick={() => setIsOpen(false)}>
                  <span className="mobile-link-icon">👤</span>
                  Profile
                </Link>
                <Link to="/settings" className="mobile-link" onClick={() => setIsOpen(false)}>
                  <span className="mobile-link-icon">⚙️</span>
                  Settings
                </Link>
                <Link to="/yield" className="mobile-link" onClick={() => setIsOpen(false)}>
                  <span className="mobile-link-icon">🌱</span>
                  Yield Dashboard
                </Link>
                <button onClick={handleLogout} className="mobile-link logout">
                  <span className="mobile-link-icon">🚪</span>
                  Logout
                </button>
              </>
            ) : null}
          </div>

          <div className="mobile-menu-footer">
            <div className="mobile-balance">
              <span>Balance</span>
              <span className="mobile-balance-amount">$0.00</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
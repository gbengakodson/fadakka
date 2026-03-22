import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// Update this with your current IP
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    console.log('🔄 AuthProvider mounted, token:', token ? 'exists' : 'none');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      console.log('⏹️ No token, skipping profile fetch');
      setLoading(false);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      console.log('📡 Fetching user profile...');
      const response = await axios.get(`${API_URL}/auth/profile/`);
      console.log('✅ Profile fetched:', response.data);
      setUser(response.data.user || response.data);
    } catch (error) {
      console.error('❌ Profile fetch error:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      console.log('📡 Attempting login for:', username);
      const response = await axios.post(`${API_URL}/auth/login/`, {
        username,
        password
      });

      const { access, refresh, user } = response.data;
      console.log('✅ Login successful:', user);

      localStorage.setItem('token', access);
      localStorage.setItem('refresh_token', refresh);

      axios.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      setToken(access);
      setUser(user);

      return { success: true };
    } catch (error) {
      console.error('❌ Login error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Login failed'
      };
    }
  };

  const register = async (userData) => {
    try {
      console.log('📡 Attempting registration with data:', {
        username: userData.username,
        email: userData.email,
        hasReferralCode: !!userData.referral_code,
        referralCode: userData.referral_code || 'none'
      });

      const response = await axios.post(`${API_URL}/auth/register/`, userData);

      console.log('✅ Registration successful:', response.data);

      // Check if referral was applied
      if (response.data.referral?.referred_by) {
        console.log(`✅ Referral code ${response.data.referral.referred_by} applied successfully`);
      }

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Registration error:', error.response?.data || error);

      // Handle specific referral code errors
      const errorData = error.response?.data;
      let errorMessage = 'Registration failed';

      if (errorData) {
        if (typeof errorData === 'object') {
          // Check for referral code specific errors
          if (errorData.referral_code) {
            errorMessage = `Referral code error: ${errorData.referral_code}`;
          } else {
            // Combine all error messages
            errorMessage = Object.values(errorData).flat().join(', ');
          }
        } else {
          errorMessage = errorData;
        }
      }

      return {
        success: false,
        error: errorMessage
      };
    }
  };

  const logout = () => {
    console.log('🚪 Logging out');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    // Add helper to get referral link
    getReferralLink: () => {
      if (user?.referral_code) {
        return `${window.location.origin}/register?ref=${user.referral_code}`;
      }
      return null;
    }
  };

  console.log('🔄 AuthContext state:', {
    isAuthenticated: !!user,
    loading,
    user: user?.username
  });

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
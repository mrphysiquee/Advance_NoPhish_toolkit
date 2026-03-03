import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import api from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role_name: string;
  is_active: boolean;
  created_at: string;
  telegram_chat_id?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: any) => Promise<void>;
  linkTelegram: (chatId: number) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { username, password });
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      
      message.success('Login successful!');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Login failed');
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      await api.post('/auth/register', userData);
      message.success('Registration successful! Please login.');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Registration failed');
      throw error;
    }
  };

  const linkTelegram = async (chatId: number) => {
    try {
      await api.post('/telegram/link', { chat_id: chatId });
      message.success('Telegram account linked successfully!');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to link Telegram account');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    message.success('Logged out successfully');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, linkTelegram }}>
      {children}
    </AuthContext.Provider>
  );
};
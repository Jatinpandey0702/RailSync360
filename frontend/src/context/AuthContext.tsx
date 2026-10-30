import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/api';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'PASSENGER' | 'ADMIN';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  isAdmin: false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('railsync_token'));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('railsync_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('railsync_token', newToken);
    localStorage.setItem('railsync_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('railsync_token');
    localStorage.removeItem('railsync_user');
  };

  useEffect(() => {
    if (token && !user) {
      apiClient.get('/auth/me')
        .then(res => {
          setUser(res.data);
          localStorage.setItem('railsync_user', JSON.stringify(res.data));
        })
        .catch(() => logout());
    }
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAdmin: user?.role === 'ADMIN' }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

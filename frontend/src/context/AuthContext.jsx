import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

// Supabase access tokens expire (1 hour by default); read the JWT's `exp` claim so we can sign out instead of
// letting every request fail with 401.
const tokenExpiresAt = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

const readStored = () => {
  const token = localStorage.getItem('access_token');
  const expiresAt = token && tokenExpiresAt(token);
  if (!token || (expiresAt && expiresAt <= Date.now())) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    return { token: null, user: null };
  }
  try {
    return { token, user: JSON.parse(localStorage.getItem('user')) };
  } catch {
    return { token, user: null };
  }
};

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(readStored);
  const { token, user } = session;

  useEffect(() => {
    if (token) {
      localStorage.setItem('access_token', token);
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  }, [token, user]);

  useEffect(() => {
    const expiresAt = token && tokenExpiresAt(token);
    if (!expiresAt) return undefined;
    const timer = setTimeout(() => setSession({ token: null, user: null }), Math.max(0, expiresAt - Date.now()));
    return () => clearTimeout(timer);
  }, [token]);

  const login = (newToken, userData) => setSession({ token: newToken, user: userData ?? null });
  const logout = () => setSession({ token: null, user: null });

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

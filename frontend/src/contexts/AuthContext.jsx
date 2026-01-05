import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

/**
 * Decode a JWT token to extract payload (no verification - backend verifies).
 */
function decodeJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error('Failed to decode JWT:', e);
    return null;
  }
}

/**
 * Auth provider component that manages authentication state.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('google_token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        // Clear corrupted data
        localStorage.removeItem('google_token');
        localStorage.removeItem('user');
      }
    }
    setIsLoading(false);
  }, []);

  /**
   * Handle successful Google login.
   * @param {object} credentialResponse - Response from GoogleLogin component
   */
  const login = (credentialResponse) => {
    const idToken = credentialResponse.credential;
    const decoded = decodeJwt(idToken);

    if (!decoded) {
      console.error('Failed to decode Google token');
      return;
    }

    const userData = {
      id: decoded.sub,
      email: decoded.email,
      name: decoded.name,
      picture: decoded.picture,
    };

    // Save to state
    setToken(idToken);
    setUser(userData);

    // Persist to localStorage
    // NOTE: localStorage is vulnerable to XSS attacks. For a local dev tool this is
    // acceptable, but production deployments should use httpOnly cookies instead.
    // See: https://owasp.org/www-community/attacks/xss/
    localStorage.setItem('google_token', idToken);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  /**
   * Handle logout - clear all auth state.
   */
  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('google_token');
    localStorage.removeItem('user');
  };

  const value = {
    user,
    token,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

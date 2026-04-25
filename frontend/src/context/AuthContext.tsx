import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";

// --- Tipos ---
interface AuthUser {
  access_token: string;
  expires_at: number; // timestamp en ms
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokenData: { access_token: string; expires_in: number }) => void;
  logout: () => void;
}

// --- Constantes ---
const TOKEN_KEY = "auth_token";
const TOKEN_EXPIRY_KEY = "auth_token_expiry";

// --- Context ---
const AuthContext = createContext<AuthContextType | null>(null);

// --- Provider ---
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (token && expiry) {
      const expiryNum = parseInt(expiry);
      const ahora = Date.now();
      const diff = expiryNum - ahora;

      if (diff > 0) {
        setUser({ access_token: token, expires_at: expiryNum });
      } else {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
      }
    }

    setIsLoading(false);
  }, []);

  const login = useCallback(
    ({
      access_token,
      expires_in,
    }: {
      access_token: string;
      expires_in: number;
    }) => {
      const expires_at = Date.now() + expires_in * 1000;

      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(TOKEN_EXPIRY_KEY, String(expires_at));
      setUser({ access_token, expires_at });
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// --- Hook personalizado ---
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de un <AuthProvider>");
  }
  return context;
};

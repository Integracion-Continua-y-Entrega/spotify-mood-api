import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const PKCE_VERIFIER_KEY = "spotify_pkce_verifier";
const PKCE_STATE_KEY = "spotify_pkce_state";
const API_URL = import.meta.env.VITE_API_URL;

type AuthStatus = "loading" | "error";

const clearPkceStorage = () => {
  sessionStorage.removeItem(PKCE_VERIFIER_KEY);
  sessionStorage.removeItem(PKCE_STATE_KEY);
};

export const CallbackView = () => {
  const navigate = useNavigate();
  const hasRun = useRef(false);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const handleAuth = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");
      const state = urlParams.get("state");
      const error = urlParams.get("error");

      if (error) {
        clearPkceStorage();
        navigate(`/error?reason=${error}`, { replace: true });
        return;
      }

      const storedState = sessionStorage.getItem(PKCE_STATE_KEY);
      const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);

      if (!state || state !== storedState) {
        clearPkceStorage();
        navigate("/error?reason=csrf", { replace: true });
        return;
      }

      if (!code || !verifier) {
        clearPkceStorage();
        navigate("/error?reason=missing_data", { replace: true });
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, verifier }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        clearPkceStorage();
        navigate("/home", { replace: true });
      } catch (err) {
        console.error("Error en login:", err);
        clearPkceStorage();
        setStatus("error");
      }
    };

    handleAuth();
  }, [navigate]);

  if (status === "error") {
    return (
      <div>
        <p>Hubo un problema al autenticar. Inténtalo de nuevo.</p>
        <button onClick={() => navigate("/login")}>Volver al inicio</button>
      </div>
    );
  }

  return <p>Autenticando con Spotify...</p>;
};

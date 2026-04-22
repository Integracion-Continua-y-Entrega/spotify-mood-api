import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

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
  const { login } = useAuth();
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

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            `HTTP ${response.status}: ${errorData.detail || "Unknown"}`,
          );
        }

        const data = await response.json();

        // 👇 ESTE LOG ES EL MÁS IMPORTANTE
        console.log(
          "📦 [CallbackView] Respuesta completa del backend:",
          JSON.stringify(data, null, 2),
        );
        console.log(
          "📦 [CallbackView] data.access_token:",
          data.access_token ?? "❌ UNDEFINED",
        );
        console.log(
          "📦 [CallbackView] data.expires_in:",
          data.expires_in ?? "❌ UNDEFINED",
        );

        login({
          access_token: data.access_token,
          expires_in: data.expires_in,
        });

        clearPkceStorage();
        navigate("/dashboard", { replace: true });
      } catch (err) {
        console.error("Error en autenticación:", err);
        clearPkceStorage();
        setStatus("error");
      }
    };

    handleAuth();
  }, [navigate, login]);

  if (status === "error") {
    return (
      <div>
        <p>Hubo un problema al autenticar. Inténtalo de nuevo.</p>
        <button onClick={() => navigate("/")}>Volver al inicio</button>
      </div>
    );
  }

  return <p>Autenticando con Spotify...</p>;
};

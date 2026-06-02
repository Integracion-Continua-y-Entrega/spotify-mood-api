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
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const handleAuth = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get("code");
      const state = urlParams.get("state");
      const error = urlParams.get("error");

      if (error) {
        setErrorMessage("El acceso fue denegado o hubo un error en Spotify.");
        setStatus("error");
        clearPkceStorage();
        return;
      }

      const storedState = sessionStorage.getItem(PKCE_STATE_KEY);
      const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);

      if (!state || state !== storedState) {
        setErrorMessage("Error de seguridad: La sesión no coincide.");
        setStatus("error");
        clearPkceStorage();
        return;
      }

      if (!code || !verifier) {
        setErrorMessage("Faltan datos de autenticación necesarios.");
        setStatus("error");
        clearPkceStorage();
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
            errorData.detail || "Error al conectar con el servidor.",
          );
        }

        const data = await response.json();

        login({
          access_token: data.access_token,
          expires_in: data.expires_in,
        });

        clearPkceStorage();

        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 1500);
      } catch (err: any) {
        console.error("Error en autenticación:", err);
        setErrorMessage(err.message || "Ocurrió un error inesperado.");
        setStatus("error");
        clearPkceStorage();
      }
    };

    handleAuth();
  }, [navigate, login]);

  // --- VISTA DE ERROR ---
  if (status === "error") {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl max-w-md w-full shadow-2xl">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-white text-2xl font-bold mb-2">
            ¡Ups! Algo salió mal
          </h2>
          <p className="text-zinc-400 mb-6">{errorMessage}</p>
          <button
            onClick={() => navigate("/")}
            className="w-full bg-white text-black font-bold py-3 rounded-full hover:scale-105 transition-transform"
          >
            Volver a intentar
          </button>
        </div>
      </div>
    );
  }

  // --- VISTA DE CARGA (Loading) ---
  return (
    <div className="min-h-screen bg-linear-to-b from-zinc-900 to-black flex flex-col items-center justify-center p-6">
      {/* Spinner animado estilo música */}
      <div className="relative w-24 h-24 mb-8">
        {/* Círculo exterior (pulso) */}
        <div className="absolute inset-0 rounded-full border-4 border-green-500/20 animate-ping"></div>
        {/* Spinner central */}
        <div className="absolute inset-0 rounded-full border-t-4 border-green-500 animate-spin"></div>
        {/* Icono central (opcional, puedes usar un SVG de nota musical) */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(34,197,94,0.5)]">
            <div className="w-2 h-6 bg-black mx-0.5 rounded-full animate-[bounce_1s_infinite_0.1s]"></div>
            <div className="w-2 h-8 bg-black mx-0.5 rounded-full animate-[bounce_1s_infinite_0.2s]"></div>
            <div className="w-2 h-5 bg-black mx-0.5 rounded-full animate-[bounce_1s_infinite_0.3s]"></div>
          </div>
        </div>
      </div>

      <div className="text-center">
        <h2 className="text-white text-2xl font-medium mb-2 tracking-tight">
          Sincronizando con Spotify
        </h2>
        <p className="text-zinc-500 animate-pulse">
          Preparando tus recomendaciones...
        </p>
      </div>

      {/* Barra de progreso sutil en la parte inferior */}
      <div className="fixed bottom-0 left-0 w-full h-1 bg-zinc-800">
        <div className="h-full bg-green-500 transition-all duration-2000 ease-out w-3/4"></div>
      </div>
    </div>
  );
};

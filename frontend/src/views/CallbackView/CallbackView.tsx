import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { getAccessToken } from "../../api/spotify";

export const CallbackView = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const effectRan = useRef(false);

  useEffect(() => {
    if (effectRan.current) return;
    effectRan.current = true;

    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const clientId = import.meta.env.VITE_SPOTIFY_CLIENT_ID;

    console.log("Origen actual:", window.location.origin);
    console.log("Código recibido:", code ? "SÍ" : "NO");

    if (!clientId || !code) {
      navigate("/");
      return;
    }

    const handleAuth = async () => {
      try {
        console.log("Iniciando intercambio...");
        const tokenResponse = await getAccessToken(clientId, code);
        localStorage.setItem("access_token", tokenResponse.access_token);
        navigate("/dashboard");
      } catch (err: any) {
        console.error("Fallo en CallbackView:", err.message);
        setError(err.message);
        effectRan.current = false;
      }
    };

    handleAuth();
  }, [navigate]);

  if (error) {
    return (
      <div role="alert" className="text-red-500 text-center mt-10">
        {error}
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center text-white bg-[#121212]">
      Procesando conexión con Spotify...
    </div>
  );
};

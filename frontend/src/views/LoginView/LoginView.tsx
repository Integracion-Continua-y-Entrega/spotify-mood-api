import { useState } from "react";
import { redirectToAuthCodeFlow } from "../../api/spotify";

export const LoginView = () => {
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    const clientId = import.meta.env.VITE_SPOTIFY_CLIENT_ID as
      | string
      | undefined;

    setError(null);

    try {
      if (!clientId) {
        throw new Error(
          "Configuración incompleta: VITE_SPOTIFY_CLIENT_ID no encontrado.",
        );
      }
      await redirectToAuthCodeFlow(clientId);
    } catch (err) {
      console.error("Auth Error:", err);
      setError("No se pudo conectar con Spotify. Intenta de nuevo.");
    }
  };

  return (
    <main className="flex h-screen items-center justify-center bg-[#121212] font-sans">
      <section
        className="bg-[#1DB954] p-10 rounded-2xl text-center w-80 shadow-[0_10px_25px_rgba(0,0,0,0.3)]"
        aria-labelledby="login-title"
      >
        <h1 id="login-title" className="mb-2 text-black text-3xl font-bold">
          Spotify Mood
        </h1>
        <p className="mb-6 text-[#191414] text-sm leading-relaxed">
          Conecta tu cuenta para analizar tus canciones según tu estado de
          ánimo.
        </p>

        {error && (
          <div
            className="bg-red-600 text-white p-2 rounded-lg mb-4 text-xs animate-pulse"
            role="alert"
          >
            {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          className="bg-black text-white px-8 py-3 rounded-full font-bold text-base hover:scale-105 active:scale-95 transition-transform duration-200 ease-in-out shadow-lg"
          aria-label="Iniciar sesión con Spotify"
        >
          Log in with Spotify
        </button>
      </section>
    </main>
  );
};

export default LoginView;

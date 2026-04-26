import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { redirectToAuthCodeFlow } from "../../api/spotify";

export const LoginView = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const spotifyError = searchParams.get("error");
    if (spotifyError) {
      setError(
        spotifyError === "access_denied"
          ? "Acceso denegado por el usuario."
          : "Hubo un error con Spotify.",
      );
    }

    if (isLoading) return;

    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, searchParams]);

  const handleLogin = async () => {
    try {
      const clientId = import.meta.env.VITE_SPOTIFY_CLIENT_ID;
      const redirectUri = import.meta.env.VITE_REDIRECT_URI;

      if (!clientId || !redirectUri) {
        throw new Error("Configuración incompleta (Env vars missing)");
      }

      await redirectToAuthCodeFlow({ clientId, redirectUri });
    } catch (err) {
      console.error("Login Error:", err);
      setError("No se pudo iniciar la conexión con Spotify.");
    }
  };

  // Pantalla de carga limpia
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#121212]">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-[#1DB954] border-t-transparent"></div>
      </div>
    );
  }

  return (
    <main className="flex h-screen items-center justify-center bg-[#121212] px-4 font-sans">
      <section
        className="w-full max-w-sm rounded-2xl bg-[#1DB954] p-10 text-center shadow-2xl transition-all"
        aria-labelledby="login-title"
      >
        <header>
          <h1 id="login-title" className="mb-2 text-3xl font-black text-black">
            Spotify Mood
          </h1>
          <p className="mb-8 text-sm font-medium leading-relaxed text-[#191414]/80">
            Analiza tu biblioteca musical según tu estado de ánimo.
          </p>
        </header>

        {error && (
          <div
            className="mb-6 rounded-lg bg-black/20 p-3 text-xs font-bold text-red-900 animate-in fade-in zoom-in duration-300"
            role="alert"
          >
            ⚠️ {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          className="w-full transform rounded-full bg-black px-8 py-4 text-base font-bold text-white shadow-xl transition-all duration-200 hover:scale-105 hover:bg-[#191414] active:scale-95 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 focus:ring-offset-[#1DB954]"
          aria-label="Iniciar sesión con Spotify"
        >
          Log in with Spotify
        </button>

        <footer className="mt-6">
          <p className="text-[10px] uppercase tracking-widest text-black/40">
            Powered by Spotify API
          </p>
        </footer>
      </section>
    </main>
  );
};

import { useNavigate } from "react-router-dom";
import {
  User,
  Music,
  Zap,
  Smile,
  Coffee,
  CloudRain,
  LogOut,
} from "lucide-react";
import { useUser } from "../../context/UserContext";
import { useMusic } from "../../context/MusicContext";
import { useAuth } from "../../context/AuthContext";

const MOODS = [
  {
    id: "happy",
    label: "Happy",
    color: "bg-yellow-400",
    hover: "hover:bg-yellow-500",
    icon: Smile,
    text: "text-black",
  },
  {
    id: "energetic",
    label: "Energetic",
    color: "bg-orange-500",
    hover: "hover:bg-orange-600",
    icon: Zap,
    text: "text-white",
  },
  {
    id: "relaxed",
    label: "Relaxed",
    color: "bg-blue-400",
    hover: "hover:bg-blue-500",
    icon: Coffee,
    text: "text-black",
  },
  {
    id: "melancholic",
    label: "Melancholic",
    color: "bg-purple-600",
    hover: "hover:bg-purple-700",
    icon: CloudRain,
    text: "text-white",
  },
];

export const DashboardView = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const { profile, isLoading: userLoading } = useUser();
  const { getRecommendations, isLoading: musicLoading } = useMusic();

  const handleMoodSelect = async (moodId: string) => {
    await getRecommendations(moodId);
    navigate("/recommendations");
  };

  if (userLoading)
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-950 text-white">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <Music className="w-12 h-12 text-green-500 animate-bounce" />
          <p className="text-zinc-400">Sincronizando con Spotify...</p>
        </div>
      </div>
    );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 md:p-10">
      {/* SECCIÓN SUPERIOR: Perfil real desde el Contexto */}
      <header className="flex items-center justify-between mb-12">
        <div className="flex items-center gap-4">
          <div className="relative">
            {profile?.profile_image ? (
              <img
                src={profile.profile_image}
                alt={profile.display_name || "Usuario"}
                className="w-14 h-14 rounded-full border-2 border-green-500 object-cover"
              />
            ) : (
              <div className="w-14 h-14 rounded-full bg-zinc-800 flex items-center justify-center border-2 border-zinc-700">
                <User className="w-8 h-8 text-zinc-500" />
              </div>
            )}
            <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-zinc-950 rounded-full"></div>
          </div>
          <div>
            <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">
              Bienvenido de nuevo
            </p>
            <h2 className="text-2xl font-bold">
              {profile?.display_name || "Melómano"}
            </h2>
          </div>
        </div>

        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-red-900/40 hover:text-red-400 rounded-full text-sm font-semibold transition-all"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </header>

      <main className="max-w-5xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-black mb-4">
            ¿Cómo suena tu día hoy?
          </h1>
          <p className="text-zinc-400 text-lg">
            Selecciona un estado de ánimo para generar una lista personalizada.
          </p>
        </div>

        {/* Grid de Moods */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {MOODS.map((mood) => {
            const Icon = mood.icon;
            return (
              <button
                key={mood.id}
                onClick={() => handleMoodSelect(mood.id)}
                disabled={musicLoading}
                className={`
                  ${mood.color} ${mood.hover} ${mood.text}
                  relative group overflow-hidden rounded-3xl p-8 h-64
                  flex flex-col items-start justify-between
                  transition-all duration-300 transform hover:-translate-y-2 hover:shadow-2xl
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                <Icon className="w-12 h-12 opacity-80 group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <span className="block text-xs uppercase font-bold tracking-widest opacity-70 mb-1">
                    Mood
                  </span>
                  <span className="text-3xl font-black">{mood.label}</span>
                </div>
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl group-hover:bg-white/20 transition-colors"></div>
              </button>
            );
          })}
        </div>

        {/* Loading de recomendaciones */}
        {musicLoading && (
          <div className="mt-12 flex flex-col items-center gap-3 text-green-400 animate-pulse">
            <div className="flex gap-1">
              <div className="w-2 h-8 bg-current rounded-full animate-bounce [animation-delay:-0.3s]"></div>
              <div className="w-2 h-8 bg-current rounded-full animate-bounce [animation-delay:-0.15s]"></div>
              <div className="w-2 h-8 bg-current rounded-full animate-bounce"></div>
            </div>
            <p className="font-medium text-zinc-400">Analizando tu vibra...</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardView;

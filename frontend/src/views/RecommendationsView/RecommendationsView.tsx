import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMusic } from "../../context/MusicContext";
import { Track } from "../../types/track";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import {
  Heart,
  ThumbsDown,
  SkipForward,
  Play,
  Clock,
  ChevronLeft,
} from "lucide-react";

export const RecommendationsView = () => {
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const navigate = useNavigate();
  const { recommendations, currentMood, isLoading, error } = useMusic();

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${Number(seconds) < 10 ? "0" : ""}${seconds}`;
  };

  const radarData = useMemo(() => {
    if (!recommendations || recommendations.length === 0) return [];

    const avg = (key: keyof Track["acoustic_features"]) =>
      recommendations.reduce((acc, t) => acc + t.acoustic_features[key], 0) /
      recommendations.length;

    return [
      { subject: "Energía", A: avg("energy") },
      { subject: "Danceability", A: avg("danceability") },
      { subject: "Valencia", A: avg("valence") },
      { subject: "Acústica", A: avg("acousticness") },
      { subject: "Instrumental", A: avg("instrumentalness") },
    ];
  }, [recommendations]);

  const handleFeedback = (
    trackId: string,
    type: "like" | "dislike" | "skip",
  ) => {
    setFeedback((prev) => ({ ...prev, [trackId]: type }));
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-zinc-950 text-white">
        <div className="flex gap-1 mb-4">
          <div className="w-2 h-8 bg-green-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-2 h-8 bg-green-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-2 h-8 bg-green-500 rounded-full animate-bounce"></div>
        </div>
        <p className="text-zinc-400 font-medium">
          Buscando el ritmo perfecto...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-zinc-950 text-white">
        <div className="bg-red-500/10 border border-red-500 p-6 rounded-2xl text-center">
          <p className="text-red-500 font-bold mb-4">⚠️ Ops! {error}</p>
          <button
            onClick={() => navigate("/dashboard")}
            className="text-sm underline"
          >
            Reintentar desde el Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!currentMood && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-zinc-950 text-white">
        <p className="text-zinc-500 mb-4">
          No has seleccionado un estado de ánimo aún.
        </p>
        <button
          onClick={() => navigate("/dashboard")}
          className="bg-green-600 hover:bg-green-500 px-6 py-2 rounded-full font-bold transition-colors"
        >
          Ir a seleccionar uno
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-4 md:p-8">
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-2 text-zinc-400 hover:text-white mb-8 group"
      >
        <ChevronLeft className="group-hover:-translate-x-1 transition-transform" />
        Volver al Dashboard
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-zinc-900/50 p-6 rounded-3xl border border-zinc-800">
            <h2 className="text-sm uppercase tracking-[0.2em] text-zinc-500 font-bold mb-2">
              Análisis del Mood
            </h2>
            <h1 className="text-4xl font-black capitalize mb-6 text-green-500">
              {currentMood}
            </h1>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart
                  cx="50%"
                  cy="50%"
                  outerRadius="80%"
                  data={radarData}
                >
                  <PolarGrid stroke="#3f3f46" />
                  <PolarAngleAxis
                    dataKey="subject"
                    tick={{ fill: "#a1a1aa", fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={30}
                    domain={[0, 1]}
                    tick={false}
                    axisLine={false}
                  />
                  <Radar
                    name="Mood Profile"
                    dataKey="A"
                    stroke="#22c55e"
                    fill="#22c55e"
                    fillOpacity={0.5}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <p className="text-zinc-400 text-sm mt-4 leading-relaxed">
              Este gráfico representa el ADN musical de tu selección actual
              basado en los atributos de Spotify.
            </p>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-zinc-900/30 rounded-3xl border border-zinc-800 overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <h3 className="font-bold text-xl">Tu Mix Personalizado</h3>
              <span className="text-zinc-500 text-sm">
                {recommendations?.length ?? 0} canciones
              </span>
            </div>

            <div className="divide-y divide-zinc-800">
              {recommendations?.map((track: Track, index: number) => (
                <div
                  key={track._id}
                  className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group"
                >
                  <span className="text-zinc-600 font-mono w-4">
                    {index + 1}
                  </span>

                  <div className="relative w-12 h-12 bg-zinc-800 rounded flex items-center justify-center overflow-hidden">
                    <Play className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity absolute z-10" />
                    <Music className="w-6 h-6 text-zinc-600 group-hover:opacity-20" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold truncate">{track.title}</h4>
                    <p className="text-zinc-500 text-sm truncate">
                      {track.artist} • {track.album}
                    </p>
                  </div>

                  <div className="hidden md:flex items-center gap-2 text-zinc-500 text-sm mr-4">
                    <Clock className="w-3 h-3" />
                    {formatTime(track.duration_ms)}
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleFeedback(track._id, "like")}
                      className={`p-2 rounded-full transition-colors ${feedback[track._id] === "like" ? "text-green-500 bg-green-500/10" : "hover:bg-zinc-800 text-zinc-500"}`}
                    >
                      <Heart
                        className={`w-5 h-5 ${feedback[track._id] === "like" ? "fill-current" : ""}`}
                      />
                    </button>
                    <button
                      onClick={() => handleFeedback(track._id, "dislike")}
                      className={`p-2 rounded-full transition-colors ${feedback[track._id] === "dislike" ? "text-red-500 bg-red-500/10" : "hover:bg-zinc-800 text-zinc-500"}`}
                    >
                      <ThumbsDown className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleFeedback(track._id, "skip")}
                      className="p-2 rounded-full hover:bg-zinc-800 text-zinc-500 transition-colors"
                    >
                      <SkipForward className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Music = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
    />
  </svg>
);

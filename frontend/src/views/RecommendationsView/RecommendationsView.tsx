import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMusic } from "../../context/MusicContext";
import { Track } from "../../types/track";
import { TrackPlayer } from "../../components/TrackPlayer/TrackPlayer";
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
  Pause,
  Clock,
  ChevronLeft,
} from "lucide-react";

export const RecommendationsView = () => {
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [activeTrackId, setActiveTrackId] = useState<string | null>(null); // Estado: Track seleccionado
  const [isPlaying, setIsPlaying] = useState<boolean>(false); // Estado: Play/Pause global

  const navigate = useNavigate();
  const { recommendations, currentMood, isLoading, error } = useMusic();

  /**
   * ⚡ EXTRACCIÓN Y APLANADO DE TRACKS (Defensivo)
   * Transforma la estructura de Recomendaciones hidratada por el Backend
   * a una lista plana de objetos Track legibles por el componente.
   */
  const tracks = useMemo(() => {
    if (!recommendations || recommendations.length === 0) return [];

    let processedTracks: any[] = [];

    if (Array.isArray(recommendations)) {
      // Caso A: El contexto guarda directamente la colección sin desestructurar el array [Recommendation]
      if ((recommendations[0] as any)?.tracks) {
        processedTracks = (recommendations[0] as any).tracks.map(
          (item: any) => item.track_details,
        );
      } else {
        // Caso B: El contexto guarda la lista directa de RecommendedTrack
        processedTracks = recommendations.map(
          (item: any) => item.track_details || item,
        );
      }
    }

    // Filtramos elementos nulos o tracks que no posean métricas de audio válidas
    return processedTracks.filter(
      (t): t is Track => !!t && !!t.acoustic_features,
    );
  }, [recommendations]);

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${Number(seconds) < 10 ? "0" : ""}${seconds}`;
  };

  // Encontrar los metadatos completos del track activo para el Player flotante
  const activeTrack = useMemo(() => {
    return tracks.find((t) => t._id === activeTrackId);
  }, [tracks, activeTrackId]);

  /**
   * 📊 PROCESAMIENTO SEGURO DEL RADAR (TypeScript Safe)
   * Usa la lista aplanada y limpia para evitar errores de división por cero
   * u objetos potencialmente 'null/undefined' dentro del reduce.
   */
  const radarData = useMemo(() => {
    const localTracks = tracks;

    if (!localTracks || localTracks.length === 0) return [];

    const avg = (key: keyof Track["acoustic_features"]) => {
      const sum = localTracks.reduce((acc, t) => {
        const val = t.acoustic_features?.[key];
        return acc + (typeof val === "number" ? val : 0);
      }, 0);
      return sum / localTracks.length;
    };

    return [
      { subject: "Energía", A: avg("energy") },
      { subject: "Danceability", A: avg("danceability") },
      { subject: "Valencia", A: avg("valence") },
      { subject: "Acústica", A: avg("acousticness") },
      { subject: "Instrumental", A: avg("instrumentalness") },
    ];
  }, [tracks]);

  // Manejador del click de reproducción por fila
  const handleTrackPlayToggle = (trackId: string) => {
    if (activeTrackId === trackId) {
      setIsPlaying(!isPlaying); // Mismo track: alterna play/pause
    } else {
      setActiveTrackId(trackId); // Nuevo track: lo selecciona y activa play
      setIsPlaying(true);
    }
  };

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
    <div className="min-h-screen bg-zinc-950 text-white p-4 md:p-8 pb-28">
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
                {tracks.length} canciones
              </span>
            </div>

            <div className="divide-y divide-zinc-800">
              {tracks.map((track: Track, index: number) => {
                const isCurrentTrack = activeTrackId === track._id;
                const isCurrentPlaying = isCurrentTrack && isPlaying;

                return (
                  <div
                    key={track._id}
                    className="p-4 flex items-center gap-4 hover:bg-white/5 transition-colors group"
                  >
                    <span className="text-zinc-600 font-mono w-4">
                      {index + 1}
                    </span>

                    {/* Botón interactivo de reproducción en la fila */}
                    <button
                      onClick={() => handleTrackPlayToggle(track._id)}
                      disabled={!track.preview_url}
                      className={`relative w-12 h-12 bg-zinc-800 rounded flex items-center justify-center overflow-hidden group/btn border border-transparent transition-colors ${track.preview_url ? "cursor-pointer hover:border-green-500/50" : "cursor-not-allowed opacity-40"}`}
                      title={
                        !track.preview_url
                          ? "Preview no disponible"
                          : "Reproducir preview"
                      }
                    >
                      {isCurrentPlaying ? (
                        <>
                          {/* Ecualizador de barras animadas */}
                          <div className="flex gap-0.5 items-end h-4 z-10 group-hover/btn:opacity-0 transition-opacity">
                            <div className="w-0.5 h-full bg-green-500 animate-[bounce_0.8s_infinite_0.1s]"></div>
                            <div className="w-0.5 h-3 bg-green-500 animate-[bounce_0.8s_infinite_0.3s]"></div>
                            <div className="w-0.5 h-4 bg-green-500 animate-[bounce_0.8s_infinite_0.2s]"></div>
                          </div>
                          <Pause className="w-5 h-5 text-white opacity-0 group-hover/btn:opacity-100 transition-opacity absolute z-10 fill-current" />
                        </>
                      ) : (
                        <Play
                          className={`w-5 h-5 transition-opacity absolute z-10 fill-current ${isCurrentTrack ? "opacity-100 text-green-500" : "text-white opacity-0 group-hover/btn:opacity-100"}`}
                        />
                      )}
                      <Music
                        className={`w-6 h-6 text-zinc-600 transition-opacity ${isCurrentPlaying ? "opacity-0" : "group-hover/btn:opacity-20"}`}
                      />
                    </button>

                    <div className="flex-1 min-w-0">
                      <h4
                        className={`font-semibold truncate transition-colors ${isCurrentTrack ? "text-green-500" : "text-white"}`}
                      >
                        {track.title}
                      </h4>
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
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* REPRODUCTOR FLOTANTE MAESTRO (Fijo en la esquina inferior derecha) */}
      {activeTrack && (
        <div className="fixed bottom-6 right-6 z-50 shadow-2xl transition-all duration-300 transform scale-100 animate-in fade-in slide-in-from-bottom-5">
          <TrackPlayer
            previewUrl={activeTrack.preview_url}
            title={activeTrack.title}
            artist={activeTrack.artist}
            isPlaying={isPlaying}
            onPlayToggle={() => setIsPlaying(!isPlaying)}
          />
        </div>
      )}
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

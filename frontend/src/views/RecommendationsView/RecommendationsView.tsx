import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMusic } from "../../context/MusicContext";
import { usePlayback } from "../../context/PlaybackContext";
import { Track } from "../../types/track";
import { TrackPlayer } from "../../components/TrackPlayer/TrackPlayer";
import { ExportPlaylistModal } from "../../components/ExportPlaylistModal/ExportPlaylistModal";
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
  const [activeTrackId, setActiveTrackId] = useState<string | null>(null);

  // ⚡ NUEVO: Estado para controlar los IDs de las canciones seleccionadas para la playlist
  const [selectedTrackIds, setSelectedTrackIds] = useState<string[]>([]);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const navigate = useNavigate();

  const { recommendations, currentMood, isLoading, error, saveTrackFeedback } =
    useMusic();

  const {
    isReady,
    isPlaying: sdkIsPlaying,
    playTrack,
    pauseTrack,
    player,
  } = usePlayback();

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${Number(seconds) < 10 ? "0" : ""}${seconds}`;
  };

  // Encontrar los metadatos completos del track activo para el Player flotante
  const activeTrack = useMemo(() => {
    return recommendations?.find((t) => t._id === activeTrackId);
  }, [recommendations, activeTrackId]);

  // ⚡ NUEVO: Memoriza y filtra únicamente los tracks que el usuario seleccionó para exportar
  const selectedTracks = useMemo(() => {
    return (
      recommendations?.filter((t) => selectedTrackIds.includes(t._id)) ?? []
    );
  }, [recommendations, selectedTrackIds]);

  /**
   * ⚡ NUEVO: Controlador para añadir o remover canciones del set de exportación
   * Pone un tope estricto en 10 elementos para coincidir con las reglas de Pydantic
   */
  const toggleTrackSelection = (trackId: string) => {
    setSelectedTrackIds((prev) => {
      if (prev.includes(trackId)) {
        return prev.filter((id) => id !== trackId);
      }
      if (prev.length >= 10) return prev; // Bloquea la selección si ya hay 10
      return [...prev, trackId];
    });
  };

  /**
   * 📊 PROCESAMIENTO SEGURO DEL RADAR (TypeScript Safe)
   */
  const radarData = useMemo(() => {
    const localTracks = recommendations;

    if (!localTracks || localTracks.length === 0) return [];

    const validTracks = localTracks.filter(
      (t): t is Track => !!t && !!t.acoustic_features,
    );

    if (validTracks.length === 0) return [];

    const avg = (key: keyof Track["acoustic_features"]) => {
      const sum = validTracks.reduce((acc, t) => {
        const val = t.acoustic_features?.[key];
        return acc + (typeof val === "number" ? val : 0);
      }, 0);
      return sum / validTracks.length;
    };

    return [
      { subject: "Energía", A: avg("energy") },
      { subject: "Danceability", A: avg("danceability") },
      { subject: "Valencia", A: avg("valence") },
      { subject: "Acústica", A: avg("acousticness") },
      { subject: "Instrumental", A: avg("instrumentalness") },
    ];
  }, [recommendations]);

  // Manejador asíncrono que dispara comandos reales al SDK de Spotify
  const handleTrackPlayToggle = async (track: Track) => {
    if (!isReady) return;

    const trackUri = `spotify:track:${track.external_ids?.spotify_id}`;
    if (!track.external_ids?.spotify_id) return;

    try {
      if (activeTrackId === track._id) {
        if (sdkIsPlaying) {
          await pauseTrack();
        } else {
          if (player) {
            await player.resume();
          } else {
            await playTrack(trackUri);
          }
        }
      } else {
        setActiveTrackId(track._id);
        await playTrack(trackUri);
      }
    } catch (err) {
      console.error("Error al controlar la reproducción desde la lista:", err);
    }
  };

  const handleFeedback = async (
    trackId: string,
    type: "like" | "dislike" | "skip",
  ) => {
    setFeedback((prev) => ({ ...prev, [trackId]: type }));
    try {
      await saveTrackFeedback(trackId, type);
    } catch (err) {
      console.error("Error al guardar la interacción del usuario:", err);
    }
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
            {/* Cabecera de la tabla con contador e indicador dinámico */}
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center gap-4 flex-wrap">
              <div>
                <h3 className="font-bold text-xl">Tu Mix Personalizado</h3>
                <p className="text-zinc-500 text-sm mt-1">
                  Selecciona{" "}
                  <span className="text-green-500 font-bold">
                    exactamente 10 canciones
                  </span>{" "}
                  para exportar
                </p>
              </div>

              {/* ⚡ MODIFICADO: El botón solo se habilita si hay exactamente 10 seleccionadas */}
              <button
                onClick={() => setIsExportModalOpen(true)}
                disabled={selectedTrackIds.length !== 10}
                className="bg-green-600 hover:bg-green-500 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold px-5 py-2.5 rounded-full transition-all shadow-lg flex items-center gap-2"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.586 14.424c-.18.295-.565.387-.86.207-2.377-1.454-5.37-1.783-8.893-.982-.336.075-.668-.135-.744-.47-.075-.336.135-.668.47-.743 3.856-.88 7.15-.505 9.822 1.13.295.178.387.563.205.858zm1.225-2.72c-.227.367-.707.487-1.074.26-2.72-1.672-6.87-2.157-10.082-1.182-.413.125-.847-.107-.972-.52-.125-.413.108-.847.52-.972 3.673-1.114 8.235-.574 11.347 1.34.37.226.49.707.26 1.074zm.105-2.822c-3.26-1.936-8.65-2.115-11.782-1.164-.5.15-1.023-.13-1.174-.633-.15-.5.13-1.023.633-1.174 3.634-1.103 9.57-.893 13.327 1.336.45.267.6.845.334 1.295-.267.45-.845.6-1.295.334z" />
                </svg>
                Exportar ({selectedTrackIds.length}/10)
              </button>
            </div>

            <div className="divide-y divide-zinc-800">
              {recommendations?.map((track: Track, index: number) => {
                const isCurrentTrack = activeTrackId === track._id;
                const isCurrentPlaying = isCurrentTrack && sdkIsPlaying;
                const hasValidSpotifyId = !!track.external_ids?.spotify_id;

                // Estados de selección por fila
                const isSelected = selectedTrackIds.includes(track._id);
                const isSelectionDisabled =
                  !isSelected && selectedTrackIds.length >= 10;

                return (
                  <div
                    key={track._id}
                    className={`p-4 flex items-center gap-4 transition-colors group ${isSelected ? "bg-green-500/5 hover:bg-green-500/10" : "hover:bg-white/5"}`}
                  >
                    {/* ⚡ NUEVO: Checkbox interactivo de control */}
                    <div className="flex items-center justify-center pl-1">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={isSelectionDisabled}
                        onChange={() => toggleTrackSelection(track._id)}
                        className="w-4 h-4 accent-green-500 cursor-pointer rounded bg-zinc-800 border-zinc-700 disabled:opacity-20 disabled:cursor-not-allowed"
                        title={
                          isSelectionDisabled
                            ? "Llegaste al límite de 10 canciones"
                            : "Seleccionar para la playlist"
                        }
                      />
                    </div>

                    <span className="text-zinc-600 font-mono w-4 text-center text-xs">
                      {index + 1}
                    </span>

                    {/* Botón interactivo de reproducción en la fila */}
                    <button
                      onClick={() => handleTrackPlayToggle(track)}
                      disabled={!hasValidSpotifyId || !isReady}
                      className={`relative w-12 h-12 bg-zinc-800 rounded flex items-center justify-center overflow-hidden group/btn border border-transparent transition-colors ${hasValidSpotifyId && isReady ? "cursor-pointer hover:border-green-500/50" : "cursor-not-allowed opacity-40"}`}
                      title={
                        !hasValidSpotifyId
                          ? "ID de catálogo no disponible"
                          : !isReady
                            ? "Conectando dispositivo de audio..."
                            : "Reproducir en Spotify Premium"
                      }
                    >
                      {isCurrentPlaying ? (
                        <>
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
                        className={`font-semibold truncate transition-colors ${isCurrentTrack ? "text-green-500 font-bold" : "text-white"}`}
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

      {/* REPRODUCTOR FLOTANTE MAESTRO ENLAZADO AL SDK */}
      {activeTrack && (
        <div className="fixed bottom-6 right-6 z-50 shadow-2xl transition-all duration-300 transform scale-100 animate-in fade-in slide-in-from-bottom-5">
          <TrackPlayer
            trackUri={`spotify:track:${activeTrack.external_ids?.spotify_id}`}
            title={activeTrack.title}
            artist={activeTrack.artist}
            durationMs={activeTrack.duration_ms}
            isPlaying={sdkIsPlaying}
            onPlayToggle={async () => {
              if (sdkIsPlaying) {
                await pauseTrack();
              } else if (player) {
                await player.resume();
              }
            }}
          />
        </div>
      )}

      {/* ⚡ MODIFICADO: Inyectamos el Modal pasándole estrictamente el array 'selectedTracks' de 10 elementos */}
      <ExportPlaylistModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        defaultName={`${currentMood ? currentMood.charAt(0).toUpperCase() + currentMood.slice(1) : "My"} Mood Mix`}
        tracksToExport={selectedTracks}
      />
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

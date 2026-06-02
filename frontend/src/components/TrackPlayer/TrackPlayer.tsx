import { useEffect, useState } from "react";
import { usePlayback } from "../../context/PlaybackContext"; // 👈 IMPORTADO: Tu nuevo contexto premium

interface TrackPlayerProps {
  trackUri: string | null | undefined; // 👈 CAMBIADO: Ahora recibe el URI oficial (ej: spotify:track:ID)
  title: string;
  artist: string;
  durationMs: number; // 👈 NUEVO: Necesario para calcular el porcentaje de la barra de progreso
  isPlaying: boolean;
  onPlayToggle: () => void;
}

export const TrackPlayer = ({
  trackUri,
  title,
  artist,
  durationMs,
  isPlaying,
  onPlayToggle,
}: TrackPlayerProps) => {
  const { playTrack, pauseTrack, isReady } = usePlayback(); // Consumimos el estado del dispositivo virtual
  const [positionMs, setPositionMs] = useState(0);

  // 1. ⏱️ RELOJ DE PREDICCIÓN INTERNA (Buttery-Smooth Progress)
  // Incrementa la barra de progreso localmente cada 500ms si la canción está activa
  useEffect(() => {
    // 💡 CORREGIDO: Usamos ReturnType para que TypeScript infiera el tipo nativo del navegador automáticamente
    let intervalId: ReturnType<typeof setInterval>;

    if (isPlaying) {
      intervalId = setInterval(() => {
        setPositionMs((prevPosition) => {
          if (prevPosition >= durationMs) {
            clearInterval(intervalId);
            return durationMs;
          }
          return prevPosition + 500; // Incremento controlado de medio segundo
        });
      }, 500);
    }

    return () => clearInterval(intervalId);
  }, [isPlaying, durationMs]);

  // 2. 🔄 RESET DE POSICIÓN
  // Si el usuario cambia de canción en la lista, reiniciamos la barra a cero inmediatamente
  useEffect(() => {
    setPositionMs(0);
  }, [trackUri]);

  // Calcular el porcentaje de progreso de forma segura evitando divisiones por cero
  const progressPercentage = durationMs > 0 ? (positionMs / durationMs) * 100 : 0;

  // Manejador centralizado de clicks que dispara los comandos al SDK
  const handlePlaybackToggle = async () => {
    if (!isReady || !trackUri) return;

    try {
      if (isPlaying) {
        await pauseTrack();
      } else {
        await playTrack(trackUri);
      }
      onPlayToggle(); // Sincroniza el estado del componente padre (RecommendationsView)
    } catch (error) {
      console.error("Error al interactuar con el Web Playback SDK:", error);
    }
  };

  // --- VISTA DESHABILITADA (Si el dispositivo no está listo o no hay canción válida) ---
  if (!trackUri || !isReady) {
    return (
      <div
        className="w-9 h-9 bg-zinc-800/40 rounded-full flex items-center justify-center text-zinc-600 cursor-not-allowed"
        title={!isReady ? "Conectando con el dispositivo de Spotify..." : "Muestra de audio no disponible"}
      >
        <svg className="w-4 h-4 fill-current animate-pulse" viewBox="0 0 24 24">
          <path d="M4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73 4.27 3zM12 4L9.91 6.09 12 8.18V4zM16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.21.05-.42.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800/80 px-3 py-2 rounded-xl w-full max-w-xs transition-all hover:border-zinc-700 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-bottom-3 duration-300">
      {/* Botón Control Play/Pause */}
      <button
        onClick={handlePlaybackToggle}
        className="w-9 h-9 bg-green-500 text-black rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-transform cursor-pointer shadow-[0_0_15px_rgba(34,197,94,0.25)]"
      >
        {isPlaying ? (
          <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4 fill-current ml-0.5" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      {/* Metadatos y Deslizador de Progreso */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-col">
          <span className="text-white text-xs font-semibold truncate select-none">
            {title}
          </span>
          <span className="text-zinc-400 text-[11px] truncate select-none">
            {artist}
          </span>
        </div>

        {/* Barra de Progreso */}
        <div className="w-full h-1 bg-zinc-800 rounded-full mt-1.5 overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};
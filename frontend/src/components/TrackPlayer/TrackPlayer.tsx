import { useEffect, useRef, useState } from "react";

interface TrackPlayerProps {
  previewUrl: string | null | undefined;
  title: string;
  artist: string;
  isPlaying: boolean;
  onPlayToggle: () => void;
}

export const TrackPlayer = ({
  previewUrl,
  title,
  artist,
  isPlaying,
  onPlayToggle,
}: TrackPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [progress, setProgress] = useState(0);

  // 1. Efecto para inicializar y limpiar el objeto de audio nativo del navegador
  useEffect(() => {
    if (!previewUrl) return;

    // Crear la instancia de audio si no existe
    if (!audioRef.current) {
      audioRef.current = new Audio(previewUrl);

      // Evento para actualizar la barra de progreso
      audioRef.current.ontimeupdate = () => {
        if (audioRef.current) {
          const current = audioRef.current.currentTime;
          const duration = audioRef.current.duration || 30; // Previews de Spotify duran 30s
          setProgress((current / duration) * 100);
        }
      };

      // Evento para cuando la canción termine sola
      audioRef.current.onended = () => {
        setProgress(0);
        if (isPlaying) onPlayToggle(); // Notifica al padre para cambiar el estado a pausado
      };
    }

    // Limpieza de memoria al desmontar el componente o cambiar de canción
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [previewUrl]);

  // 2. Efecto para reaccionar a los comandos de Play/Pause globales del padre
  useEffect(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.play().catch((err) => {
        console.error("Error al reproducir el preview de audio:", err);
        onPlayToggle(); // Revierte el estado en el padre si el navegador bloquea el auto-play
      });
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying]);

  // Si no hay preview disponible por parte de Spotify, mostramos un estado deshabilitado sutil
  if (!previewUrl) {
    return (
      <div
        className="w-9 h-9 bg-zinc-800/40 rounded-full flex items-center justify-center text-zinc-600 cursor-not-allowed"
        title="Preview no disponible para esta canción"
      >
        <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
          <path d="M4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73 4.27 3zM12 4L9.91 6.09 12 8.18V4zM16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.21.05-.42.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800/80 px-3 py-2 rounded-xl w-full max-w-xs transition-all hover:border-zinc-700">
      {/* Botón Play/Pause */}
      <button
        onClick={onPlayToggle}
        className="w-9 h-9 bg-green-500 text-black rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-transform cursor-pointer shadow-[0_0_15px_rgba(34,197,94,0.2)]"
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

      {/* Título, Artista y Mini Barra de Progreso */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-col">
          <span className="text-white text-xs font-semibold truncate">
            {title}
          </span>
          <span className="text-zinc-400 text-[11px] truncate">{artist}</span>
        </div>

        {/* Barra de Progreso del Buffer */}
        <div className="w-full h-1 bg-zinc-800 rounded-full mt-1.5 overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-100 ease-linear"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

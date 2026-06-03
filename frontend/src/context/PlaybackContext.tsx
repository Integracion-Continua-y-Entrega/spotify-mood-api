import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useAuth } from "./AuthContext"; 

interface PlaybackContextType {
  player: Spotify.Player | null;
  deviceId: string | null;
  isReady: boolean;
  isPlaying: boolean;
  currentTrack: Spotify.Track | null;
  playTrack: (trackUri: string) => Promise<void>;
  pauseTrack: () => Promise<void>;
}

const PlaybackContext = createContext<PlaybackContextType | null>(null);

export const PlaybackProvider = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();

  const [player, setPlayer] = useState<Spotify.Player | null>(null);
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<Spotify.Track | null>(null);

  // 1. Inicialización y control del ciclo de vida del SDK
  useEffect(() => {
    // ⚡ CAMBIADO: Leemos explícitamente el token de Spotify auténtico
    const token = localStorage.getItem("spotify_access_token") || ""; 

    console.log("🔍 Intentando inicializar Spotify SDK...", { 
      isAuthenticated, 
      hasToken: !!token,
      tokenLength: token?.length 
    });

    if (!isAuthenticated || !token) {
      console.warn("⚠️ Abortando inicialización: No estás autenticado o el token de Spotify está vacío.");
      return;
    }

    window.onSpotifyWebPlaybackSDKReady = () => {
      console.log("📦 El script de Spotify ha respondido. Creando instancia del Player...");
      
      const spotifyPlayer = new window.Spotify.Player({
        name: "UV Connect Mood Player",
        getOAuthToken: (cb: (t: string) => void) => {
          const freshToken = localStorage.getItem("spotify_access_token") || token;
          cb(freshToken);
        },
        volume: 0.5,
      });

      // --- LISTENERS DE ESTADO Y EVENTOS ---
      spotifyPlayer.addListener("ready", ({ device_id }) => {
        console.log("🟢 Spotify Web Playback SDK Listo con ID de Dispositivo:", device_id);
        setDeviceId(device_id);
        setIsReady(true);
      });

      spotifyPlayer.addListener("not_ready", ({ device_id }) => {
        console.warn("🔴 El dispositivo de Spotify se ha desconectado:", device_id);
        setIsReady(false);
        setDeviceId(null);
      });

      spotifyPlayer.addListener("player_state_changed", (state) => {
        if (!state) return;
        setIsPlaying(!state.paused);
        setCurrentTrack(state.track_window.current_track);
      });

      spotifyPlayer.addListener("initialization_error", ({ message }) => console.error("❌ Error de inicialización del SDK:", message));
      spotifyPlayer.addListener("authentication_error", ({ message }) => console.error("❌ Error de autenticación (Token inválido/expirado):", message));
      spotifyPlayer.addListener("account_error", ({ message }) => {
        console.error("🔒 Error de cuenta: Se requiere obligatoriamente una cuenta Spotify Premium.", message);
      });

      spotifyPlayer.connect().then((success) => {
        if (success) console.log("🚀 Comando de conexión enviado con éxito al SDK de Spotify.");
      });

      setPlayer(spotifyPlayer);
    };

    if (window.Spotify && window.Spotify.Player) {
      console.log("🔄 El objeto window.Spotify ya existe en memoria. Inicializando reproductor directamente...");
      window.onSpotifyWebPlaybackSDKReady();
    } else if (!document.getElementById("spotify-player-sdk")) {
      console.log("➕ Inyectando el elemento <script> de Spotify en el DOM...");
      const script = document.createElement("script");
      script.id = "spotify-player-sdk";
      script.src = "https://sdk.scdn.co/spotify-player.js";
      script.async = true;
      document.body.appendChild(script);
    }

    return () => {
      if (player) {
        console.log("🔌 Desconectando y destruyendo instancia previa del player...");
        player.disconnect();
      }
    };
  }, [isAuthenticated]); 

  // 2. Método Avanzado: Reproducir un URI específico de forma reactiva
  const playTrack = useCallback(async (trackUri: string) => {
    if (!deviceId) {
      console.warn("⚠️ No se puede reproducir: El SDK aún no reporta un Device ID activo.");
      return;
    }

    // ⚡ CORREGIDO: Leer del localStorage con la clave correcta que sí tiene el token largo
    const currentToken = localStorage.getItem("spotify_access_token");
    if (!currentToken) {
      console.error("❌ Error de reproducción: No se encontró ningún token en el almacenamiento.");
      return;
    }

    try {
      // Símbolo '$' añadido correctamente para inyectar el deviceId dinámico
      await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
        method: "PUT",
        body: JSON.stringify({ uris: [trackUri] }),
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${currentToken}`, // 👈 Ahora sí viaja el token real de 259 caracteres
        },
      });
    } catch (error) {
      console.error("Error al disparar reproducción vía API de Spotify:", error);
    }
  }, [deviceId]);

  // 3. Método: Pausar de forma nativa usando la instancia del SDK
  const pauseTrack = useCallback(async () => {
    if (player) {
      await player.pause();
    }
  }, [player]);

  return (
    <PlaybackContext.Provider
      value={{
        player,
        deviceId,
        isReady,
        isPlaying,
        currentTrack,
        playTrack,
        pauseTrack,
      }}
    >
      {children}
    </PlaybackContext.Provider>
  );
};

export const usePlayback = () => {
  const context = useContext(PlaybackContext);
  if (!context) throw new Error("usePlayback debe usarse dentro de PlaybackProvider");
  return context;
};
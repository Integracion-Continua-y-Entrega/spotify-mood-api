import { createContext, useContext, useState } from "react";
import { musicService } from "../api/musicService";
import { Track } from "../types/track";

interface MusicContextType {
  recommendations: Track[];
  currentMood: string | null;
  recommendationId: string | null; // 👈 NUEVO: Almacena el _id de la sesión de recomendación actual
  getRecommendations: (mood: string) => Promise<void>;
  saveTrackFeedback: (
    trackId: string,
    feedback: "like" | "dislike" | "skip",
  ) => Promise<void>; // 👈 NUEVO: Despacha el feedback al backend
  isLoading: boolean;
  error: string | null;
}

const MusicContext = createContext<MusicContextType | null>(null);

export const MusicProvider = ({ children }: { children: React.ReactNode }) => {
  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [currentMood, setCurrentMood] = useState<string | null>(null);
  const [recommendationId, setRecommendationId] = useState<string | null>(null); // 👈 NUEVO
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendations = async (mood: string) => {
    setIsLoading(true);
    setError(null);
    setCurrentMood(mood);
    setRecommendationId(null); // Limpiamos el ID previo antes de la nueva consulta

    try {
      const recResponse = await musicService.getRecommendations(mood);
      const recData = recResponse.recommendations?.[0];

      if (!recData || !recData.tracks || recData.tracks.length === 0) {
        setRecommendations([]);
        return;
      }

      // ⚡ MEJORA: Capturamos el ID único de la recomendación antes de la hidratación
      setRecommendationId(recData._id);

      const trackIds = recData.tracks.map((t) => t.track_id);

      const tracksCompletosResponse =
        await musicService.getBulkTracks(trackIds);

      setRecommendations(tracksCompletosResponse.tracks || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al obtener recomendaciones",
      );
      console.error("MusicContext Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // ⚡ NUEVO: Registra la interacción del usuario de manera persistente en la BD
  const saveTrackFeedback = async (
    trackId: string,
    feedback: "like" | "dislike" | "skip",
  ) => {
    if (!recommendationId) {
      console.warn(
        "⚠️ No se puede guardar feedback: Falta el ID de la recomendación activa.",
      );
      return;
    }

    try {
      await musicService.updateTrackFeedback(
        recommendationId,
        trackId,
        feedback,
      );
      console.log(
        `💾 Feedback '${feedback}' guardado con éxito para el track: ${trackId}`,
      );
    } catch (err) {
      console.error("Error al persistir el feedback en el servidor:", err);
    }
  };

  return (
    <MusicContext.Provider
      value={{
        recommendations,
        currentMood,
        recommendationId, // 👈 Expuesto en el Contexto
        getRecommendations,
        saveTrackFeedback, // 👈 Expuesto en el Contexto
        isLoading,
        error,
      }}
    >
      {children}
    </MusicContext.Provider>
  );
};

export const useMusic = () => {
  const context = useContext(MusicContext);
  if (!context) throw new Error("useMusic debe usarse dentro de MusicProvider");
  return context;
};

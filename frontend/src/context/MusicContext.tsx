import { createContext, useContext, useState } from "react";
import { musicService } from "../api/musicService";
import { Track } from "../types/track";

interface MusicContextType {
  recommendations: Track[];
  currentMood: string | null;
  getRecommendations: (mood: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const MusicContext = createContext<MusicContextType | null>(null);

export const MusicProvider = ({ children }: { children: React.ReactNode }) => {
  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [currentMood, setCurrentMood] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendations = async (mood: string) => {
    setIsLoading(true);
    setError(null);
    setCurrentMood(mood);

    try {
      const recResponse = await musicService.getRecommendations(mood);
      const recData = recResponse.recommendations?.[0];

      if (!recData || !recData.tracks || recData.tracks.length === 0) {
        setRecommendations([]);
        return;
      }

      const trackIds = recData.tracks.map((t: any) => t.track_id);

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

  return (
    <MusicContext.Provider
      value={{
        recommendations,
        currentMood,
        getRecommendations,
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

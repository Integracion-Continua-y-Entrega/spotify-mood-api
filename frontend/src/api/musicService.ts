import { apiFetch } from "./client";
import { Track } from "../types/track";

interface RecommendationResponse {
  recommendations: {
    tracks: Track[];
    user_id?: string;
    generated_at?: string;
  }[];
}

export const musicService = {
  getRecommendations: (mood: string): Promise<RecommendationResponse> => {
    return apiFetch(`/users/me/recommendations?mood=${mood}`, {
      method: "POST",
    });
  },
  getBulkTracks: (ids: string[]): Promise<{ tracks: Track[] }> => {
    return apiFetch("/tracks/bulk", {
      method: "POST",
      body: JSON.stringify({ ids }),
    });
  },
};

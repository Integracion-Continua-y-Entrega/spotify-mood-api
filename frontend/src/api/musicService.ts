import { apiFetch } from "./client";
import { Track } from "../types/track";

interface RecommendationResponse {
  recommendations: {
    _id: string; // 👈 ID de la sesión de recomendación en MongoDB
    user_id?: string;
    generated_at?: string;
    query_params?: any;
    tracks: {
      track_id: string;
      score: number;
      rank: number;
      user_feedback: string | null;
      feedback_at: string | null;
    }[];
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

  // ⚡ NUEVO: Persistencia de likes, dislikes y skips en el backend
  updateTrackFeedback: (
    recId: string,
    trackId: string,
    feedback: "like" | "dislike" | "skip",
  ): Promise<{ message: string }> => {
    return apiFetch(`/recommendations/${recId}/tracks/${trackId}`, {
      method: "PATCH",
      body: JSON.stringify({ feedback: feedback.toUpperCase() }), // El backend espera USER_FEEDBACK (LIKE, DISLIKE, SKIP)
    });
  },
};

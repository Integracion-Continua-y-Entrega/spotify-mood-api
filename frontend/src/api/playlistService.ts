import { apiFetch } from "./client";

export interface CreatePlaylistPayload {
  name: string;
  description: string;
  public: boolean;
  track_ids: string[]; // Debe contener exactamente 10 IDs de MongoDB
}

export const playlistService = {
  /**
   * Crea una playlist en Spotify y la persiste en MongoDB
   */
  createPlaylist: (payload: CreatePlaylistPayload): Promise<any> => {
    return apiFetch("/users/me/playlists", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Recupera las playlists guardadas del usuario autenticado
   */
  getUserPlaylists: (): Promise<{ playlists: any[] }> => {
    return apiFetch("/users/me/playlists", {
      method: "GET",
    });
  },
};

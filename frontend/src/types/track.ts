export interface Track {
  _id: string;
  title: string;
  artist: string;
  album: string;
  duration_ms: number;
  acoustic_features: {
    energy: number;
    danceability: number;
    valence: number;
    acousticness: number;
    instrumentalness: number;
  };
}

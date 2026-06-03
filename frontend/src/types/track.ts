export interface AcousticFeatures {
  /** Nivel de intensidad y actividad de la pista (0.0 a 1.0) */
  energy: number;
  /** Qué tan apta es la canción para bailar según el ritmo y estabilidad (0.0 a 1.0) */
  danceability: number;
  /** Positividad musical / Grado de felicidad que transmite el track (0.0 a 1.0) */
  valence: number;
  /** Probabilidad de que la pista sea acústica (0.0 a 1.0) */
  acousticness: number;
  /** Probabilidad de que no contenga elementos vocales (0.0 a 1.0) */
  instrumentalness: number;
  /** Detecta la presencia de audiencia en la grabación (0.0 a 1.0) */
  liveness: number;
  /** Presencia de palabras habladas en la pista (0.0 a 1.0) */
  speechiness: number;
  /** El volumen general de la pista en decibelios (dB) */
  loudness: number;
  /** El tempo estimado de la pista en pulsaciones por minuto (BPM) */
  tempo: number;
  /** La clave (nota musical) estimada de la pista (0 = C, 1 = C♯/D♭, etc.) */
  key: number;
  /** Modalidad de la pista (0 = menor, 1 = mayor) */
  mode: number;
  /** Métrica de compás estimada (ej. 4 para un compás de 4/4) */
  time_signature?: number | null;
}

export interface ExternalIds {
  /** Identificador único de la pista en la API de Spotify */
  spotify_id: string;
  /** Código Internacional Estándar de Grabación (opcional) */
  isrc?: string | null;
}

export interface Track {
  /** ID único generado por MongoDB (_id) utilizado en el frontend */
  _id: string;
  /** Título de la canción */
  title: string;
  /** Nombre del artista o artistas (concatenados o principales) */
  artist: string;
  /** Nombre del álbum al que pertenece */
  album: string;
  /** Año de lanzamiento del álbum */
  release_year?: number | null;
  /** Duración de la pista en milisegundos */
  duration_ms: number;
  /** Lista de géneros asociados al track */
  genre?: string[] | null;
  /** Idioma detectado o asociado a la canción */
  language?: string | null;
  /** Identificadores externos de Spotify */
  external_ids: ExternalIds;
  /** Atributos y métricas de análisis de audio de Spotify */
  acoustic_features: AcousticFeatures;
  /** URL pública del clip de audio de 30 segundos de Spotify para preescuchas */
  preview_url?: string | null;
  /** Fecha y hora en la que el track fue registrado en el sistema */
  added_at?: string;
}

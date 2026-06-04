declare global {
  interface Window {
    onSpotifyWebPlaybackSDKReady: () => void;
    Spotify: typeof Spotify;
  }

  namespace Spotify {
    interface PlayerOptions {
      name: string;
      getOAuthToken: (cb: (token: string) => void) => void;
      volume?: number;
    }

    class Player {
      constructor(options: PlayerOptions);
      connect(): Promise<boolean>;
      disconnect(): void;
      getCurrentState(): Promise<PlaybackState | null>;
      getVolume(): Promise<number>;
      setVolume(volume: number): Promise<void>;
      pause(): Promise<void>;
      resume(): Promise<void>;
      togglePlay(): Promise<void>;
      seek(position_ms: number): Promise<void>;
      previousTrack(): Promise<void>;
      nextTrack(): Promise<void>;
      addListener(event: 'ready' | 'not_ready', cb: (device: { device_id: string }) => void): boolean;
      addListener(event: 'player_state_changed', cb: (state: PlaybackState | null) => void): boolean;
      addListener(event: 'initialization_error' | 'authentication_error' | 'account_error' | 'playback_error', cb: (err: { message: string }) => void): boolean;
      removeListener(event: string, cb?: Function): boolean;
    }

    interface Track {
      uri: string;
      id: string | null;
      type: 'track' | 'episode';
      media_type: 'audio' | 'video';
      name: string;
      is_playable: boolean;
      album: {
        uri: string;
        name: string;
        images: Array<{ url: string }>;
      };
       Ramos: Array<{ uri: string; name: string }>;
    }

    interface PlaybackState {
      paused: boolean;
      position: number;
      duration: number;
      track_window: {
        current_track: Track;
        next_tracks: Track[];
        previous_tracks: Track[];
      };
    }
  }
}

export {};
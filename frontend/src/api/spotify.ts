import { generateCodeVerifier, generateCodeChallenge } from "../utils/pkce";

export interface SpotifyAuthConfig {
  clientId: string;
  redirectUri: string;
  scopes?: string[];
}

const DEFAULT_SCOPES = [
  "user-read-private",
  "user-read-email",
  "user-top-read",
];
const PKCE_VERIFIER_KEY = "spotify_pkce_verifier";
const PKCE_STATE_KEY = "spotify_pkce_state";

export async function redirectToAuthCodeFlow(
  config: SpotifyAuthConfig,
): Promise<void> {
  const { clientId, redirectUri, scopes = DEFAULT_SCOPES } = config;

  if (!clientId?.trim()) {
    throw new Error("clientId es requerido para iniciar la autenticación.");
  }
  if (!redirectUri?.trim()) {
    throw new Error("redirectUri es requerido para iniciar la autenticación.");
  }

  const verifier = generateCodeVerifier(128);
  const state = crypto.randomUUID();

  let challenge: string;
  try {
    challenge = await generateCodeChallenge(verifier);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Error criptográfico en PKCE: ${message}`);
  }

  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);
  sessionStorage.setItem(PKCE_STATE_KEY, state);

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: "code",
    redirect_uri: redirectUri,
    scope: scopes.join(" "),
    code_challenge_method: "S256",
    code_challenge: challenge,
    state,
    show_dialog: "false",
  });

  window.location.href = `https://accounts.spotify.com/authorize?${params.toString()}`;
}

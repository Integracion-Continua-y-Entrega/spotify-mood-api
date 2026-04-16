import { generateCodeVerifier, generateCodeChallenge } from "../utils/pkce";

const DEFAULT_SCOPES = ["user-read-private", "user-read-email"];

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope: string;
}

export async function redirectToAuthCodeFlow(
  clientId: string,
  scopes: string[] = DEFAULT_SCOPES,
): Promise<void> {
  if (!clientId?.trim()) {
    throw new Error("clientId es requerido para iniciar la autenticación.");
  }

  const verifier = generateCodeVerifier(128);
  let challenge: string;

  try {
    challenge = await generateCodeChallenge(verifier);
  } catch (error) {
    throw new Error(`Error criptográfico en PKCE: ${error}`);
  }

  sessionStorage.setItem("spotify_pkce_verifier", verifier);

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: "code",
    redirect_uri: import.meta.env.VITE_REDIRECT_URI,
    scope: scopes.join(" "),
    code_challenge_method: "S256",
    code_challenge: challenge,
  });

  window.location.href = `https://accounts.spotify.com/authorize?${params.toString()}`;
}

export async function getAccessToken(
  clientId: string,
  code: string,
): Promise<TokenResponse> {
  const verifier = sessionStorage.getItem("spotify_pkce_verifier");

  if (!verifier) {
    throw new Error(
      "PKCE verifier no encontrado. Es posible que la sesión haya expirado.",
    );
  }

  const params = new URLSearchParams({
    client_id: clientId,
    grant_type: "authorization_code",
    code,
    redirect_uri: import.meta.env.VITE_REDIRECT_URI,
    code_verifier: verifier,
  });

  const response = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });

  sessionStorage.removeItem("spotify_pkce_verifier");

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(
      `Spotify Auth Error [${response.status}]: ${errorData.error_description || errorData.error}`,
    );
  }

  return response.json() as Promise<TokenResponse>;
}

export const generateCodeVerifier = (length: number = 64): string => {
  if (length < 43 || length > 128) {
    throw new RangeError("length debe estar entre 43 y 128 (RFC 7636)");
  }
  const possible =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  const randomValues = crypto.getRandomValues(new Uint8Array(length * 2));
  let result = "";
  for (const byte of randomValues) {
    if (byte < possible.length * Math.floor(256 / possible.length)) {
      result += possible[byte % possible.length];
    }
    if (result.length === length) break;
  }
  return result;
};

export const generateCodeChallenge = async (
  codeVerifier: string,
): Promise<string> => {
  const data = new TextEncoder().encode(codeVerifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return btoa(
    Array.from(new Uint8Array(digest), (b) => String.fromCharCode(b)).join(""),
  )
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
};

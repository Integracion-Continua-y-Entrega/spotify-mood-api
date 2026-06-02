const BASE_URL = `${import.meta.env.VITE_API_URL}/api/v1`;

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem("auth_token");

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  if (!BASE_URL) {
    console.error("ERROR: VITE_BASE_URL no está definida en el archivo .env");
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_token_expiry");
    window.location.href = "/";
    return;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error("Detalle del error 422:", errorData);

    const errorMessage =
      typeof errorData.detail === "string"
        ? errorData.detail
        : JSON.stringify(errorData.detail);

    throw new Error(errorMessage || "Error en la petición");
  }

  return response.json();
};

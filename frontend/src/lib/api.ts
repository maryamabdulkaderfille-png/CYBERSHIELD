import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { getCookie } from "@/lib/cookies";

const MUTATING_METHODS = new Set(["post", "put", "patch", "delete"]);
const CSRF_EXEMPT_PATHS = ["/auth/login", "/auth/register", "/auth/refresh", "/guest/"];

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
  // Without this, a stalled request never settles its Promise at all — no
  // .then, no .catch, no .finally — so a page whose loading state depends
  // on that request (e.g. isLoading flags) can get stuck spinning forever
  // instead of eventually showing an error/empty state.
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const method = (config.method ?? "get").toLowerCase();
  const isExempt = CSRF_EXEMPT_PATHS.some((path) => config.url?.includes(path));
  if (MUTATING_METHODS.has(method) && !isExempt) {
    const csrfToken = getCookie("csrf_access_token");
    if (csrfToken) {
      config.headers.set("X-CSRF-TOKEN", csrfToken);
    }
  }
  return config;
});

let refreshPromise: Promise<void> | null = null;

async function refreshAccessToken(): Promise<void> {
  const csrfToken = getCookie("csrf_refresh_token");
  await api.post(
    "/auth/refresh",
    {},
    csrfToken ? { headers: { "X-CSRF-TOKEN": csrfToken } } : undefined
  );
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/");

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        await refreshPromise;
        return api(originalRequest);
      } catch {
        // Refresh failed — fall through and reject with the original error.
      }
    }

    return Promise.reject(error);
  }
);

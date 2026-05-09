import { apiFetch } from "./client";

export const userService = {
  getMe: () => apiFetch("/users/me"),
};

import { api } from "@/lib/api";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

export async function registerUser(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<{ user: User }>("/auth/register", payload);
  return data.user;
}

export async function loginUser(payload: LoginPayload): Promise<User> {
  const { data } = await api.post<{ user: User }>("/auth/login", payload);
  return data.user;
}

export async function logoutUser(): Promise<void> {
  await api.post("/auth/logout");
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<{ user: User }>("/users/me");
  return data.user;
}

export async function forgotPassword(email: string): Promise<void> {
  await api.post("/auth/forgot-password", { email });
}

export async function resetPassword(token: string, password: string, confirmPassword: string): Promise<void> {
  await api.post("/auth/reset-password", { token, password, confirm_password: confirmPassword });
}

export async function verifyEmail(token: string): Promise<User> {
  const { data } = await api.post<{ user: User }>("/auth/verify-email", { token });
  return data.user;
}

export async function resendVerification(email: string): Promise<void> {
  await api.post("/auth/resend-verification", { email });
}

export async function updateProfile(payload: { full_name?: string; username?: string }): Promise<User> {
  const { data } = await api.put<{ user: User }>("/users/me", payload);
  return data.user;
}

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
}): Promise<void> {
  await api.put("/users/me/password", payload);
}

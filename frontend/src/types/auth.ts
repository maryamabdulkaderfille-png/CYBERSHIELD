export type UserRole = "user" | "admin";
export type UserStatus = "active" | "suspended" | "removed";

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_verified: boolean;
  is_active: boolean;
  status: UserStatus;
  created_at: string | null;
  last_login: string | null;
  phone: string | null;
  country: string | null;
  bio: string | null;
  avatar_url: string | null;
}

export interface RegisterPayload {
  full_name: string;
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface ApiErrorBody {
  error: string;
  details?: Record<string, string[]>;
}

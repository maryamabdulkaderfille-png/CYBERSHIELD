import { api } from "@/lib/api";
import type { User } from "@/types/auth";
import type { ExtendedProfileFields, ProfileStats } from "@/types/profile";

export async function getProfile(): Promise<{ user: User; stats: ProfileStats }> {
  const { data } = await api.get<{ user: User; stats: ProfileStats }>("/profile");
  return data;
}

export async function updateExtendedProfile(payload: ExtendedProfileFields): Promise<User> {
  const { data } = await api.put<{ user: User }>("/profile", payload);
  return data.user;
}

import { api } from "@/lib/api";
import type { Session, UserSettings } from "@/types/settings";

export async function getSettings(): Promise<UserSettings> {
  const { data } = await api.get<{ settings: UserSettings }>("/settings");
  return data.settings;
}

export async function updateSettings(payload: Partial<UserSettings>): Promise<UserSettings> {
  const { data } = await api.put<{ settings: UserSettings }>("/settings", payload);
  return data.settings;
}

export async function getSessions(): Promise<Session[]> {
  const { data } = await api.get<{ sessions: Session[] }>("/settings/sessions");
  return data.sessions;
}

export async function revokeSession(sessionId: number): Promise<void> {
  await api.delete(`/settings/sessions/${sessionId}`);
}

export async function revokeOtherSessions(): Promise<number> {
  const { data } = await api.post<{ revoked_count: number }>("/settings/sessions/revoke-others");
  return data.revoked_count;
}

export async function deactivateAccount(password: string): Promise<void> {
  await api.delete("/settings/account", { data: { password } });
}

/** Always rejects with a 501 today — see the backend's settings_bp export
 * route for the prepared-but-unimplemented data-export interface. */
export async function exportMyData(): Promise<void> {
  await api.get("/settings/export");
}

import { api } from "@/lib/api";
import type { DashboardIntelligence } from "@/types/dashboardIntel";

export async function getDashboardIntelligence(): Promise<DashboardIntelligence> {
  const { data } = await api.get<DashboardIntelligence>("/dashboard");
  return data;
}

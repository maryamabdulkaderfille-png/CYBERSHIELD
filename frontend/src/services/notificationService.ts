import { api } from "@/lib/api";
import type { Notification, NotificationListResponse } from "@/types/notification";

export async function listNotifications(params: {
  page?: number;
  per_page?: number;
  unread_only?: boolean;
} = {}): Promise<NotificationListResponse> {
  const { data } = await api.get<NotificationListResponse>("/notifications", { params });
  return data;
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await api.get<{ unread_count: number }>("/notifications/unread-count");
  return data.unread_count;
}

export async function markRead(id: number): Promise<Notification> {
  const { data } = await api.put<{ notification: Notification }>(`/notifications/${id}/read`);
  return data.notification;
}

export async function markAllRead(): Promise<number> {
  const { data } = await api.put<{ updated_count: number }>("/notifications/read-all");
  return data.updated_count;
}

export async function deleteNotification(id: number): Promise<void> {
  await api.delete(`/notifications/${id}`);
}

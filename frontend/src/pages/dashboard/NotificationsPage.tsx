import { Bell, CheckCheck, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { useNotifications } from "@/context/NotificationContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { NOTIFICATION_ICON } from "@/lib/notifications";
import { formatRelativeDate } from "@/lib/risk";
import * as notificationService from "@/services/notificationService";
import type { Notification } from "@/types/notification";

const PER_PAGE = 20;

export function NotificationsPage() {
  const { refreshUnreadCount } = useNotifications();
  const { showToast } = useToast();

  const [items, setItems] = useState<Notification[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (targetPage: number, filterUnread: boolean) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await notificationService.listNotifications({
        page: targetPage,
        per_page: PER_PAGE,
        unread_only: filterUnread,
      });
      setItems(response.items);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load notifications."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load(page, unreadOnly);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, unreadOnly]);

  const handleMarkRead = async (id: number) => {
    await notificationService.markRead(id);
    setItems((current) => current.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    await refreshUnreadCount();
  };

  const handleDelete = async (id: number) => {
    await notificationService.deleteNotification(id);
    setItems((current) => current.filter((n) => n.id !== id));
    await refreshUnreadCount();
  };

  const handleMarkAllRead = async () => {
    const updated = await notificationService.markAllRead();
    if (updated > 0) {
      setItems((current) => current.map((n) => ({ ...n, is_read: true })));
      await refreshUnreadCount();
      showToast(`${updated} notification(s) marked as read.`, "success");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Notifications</h1>
          <p className="mt-1 text-sm text-slate-400">Security alerts and activity across your account.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => {
                setPage(1);
                setUnreadOnly(e.target.checked);
              }}
              className="h-4 w-4 rounded border-white/20 bg-white/5"
            />
            Unread only
          </label>
          <button onClick={handleMarkAllRead} className="btn-secondary">
            <CheckCheck size={16} />
            Mark all read
          </button>
        </div>
      </div>

      {error && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>}

      <div className="glass-card p-0">
        {isLoading ? (
          <p className="px-6 py-14 text-center text-sm text-slate-500">Loading…</p>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="No notifications"
            description="Security alerts from your scans will show up here."
          />
        ) : (
          <div>
            {items.map((notification) => {
              const Icon = NOTIFICATION_ICON[notification.type];
              return (
                <div
                  key={notification.id}
                  className={`flex items-start gap-4 border-b border-white/5 px-6 py-4 last:border-0 ${
                    notification.is_read ? "opacity-60" : ""
                  }`}
                >
                  <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5">
                    <Icon size={18} className="text-slate-300" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-100">{notification.title}</p>
                    <p className="mt-1 text-sm text-slate-500">{notification.message}</p>
                    <p className="mt-1.5 text-xs text-slate-600">{formatRelativeDate(notification.created_at)}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    {!notification.is_read && (
                      <button
                        onClick={() => handleMarkRead(notification.id)}
                        title="Mark as read"
                        className="rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-brand-cyan"
                      >
                        <CheckCheck size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(notification.id)}
                      title="Delete"
                      className="rounded-lg p-2 text-slate-500 hover:bg-danger/10 hover:text-danger"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="btn-secondary px-4 py-2 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="btn-secondary px-4 py-2 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

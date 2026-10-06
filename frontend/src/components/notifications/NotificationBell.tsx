import { AnimatePresence, motion } from "framer-motion";
import { Bell, CheckCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";

import { useNotifications } from "@/context/NotificationContext";
import { NOTIFICATION_ICON } from "@/lib/notifications";
import { formatRelativeDate } from "@/lib/risk";
import * as notificationService from "@/services/notificationService";
import type { Notification } from "@/types/notification";

export function NotificationBell() {
  const { unreadCount, refreshUnreadCount } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [panelPosition, setPanelPosition] = useState<{ top: number; right: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // The panel is rendered via a portal (see below) so it isn't clipped to
  // "z-20" by the topbar's own stacking context — position is computed from
  // the trigger button's viewport rect instead of relying on `absolute`
  // positioning within a parent that no longer contains it in the DOM.
  const updatePosition = useCallback(() => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setPanelPosition({ top: rect.bottom + 8, right: window.innerWidth - rect.right });
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      const insideTrigger = containerRef.current?.contains(target);
      const insidePanel = panelRef.current?.contains(target);
      if (!insideTrigger && !insidePanel) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    updatePosition();
    window.addEventListener("resize", updatePosition);
    return () => window.removeEventListener("resize", updatePosition);
  }, [isOpen, updatePosition]);

  const toggleOpen = async () => {
    const next = !isOpen;
    setIsOpen(next);
    if (next) {
      updatePosition();
      setIsLoading(true);
      try {
        const response = await notificationService.listNotifications({ page: 1, per_page: 5 });
        setItems(response.items);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleMarkAllRead = async () => {
    await notificationService.markAllRead();
    setItems((current) => current.map((n) => ({ ...n, is_read: true })));
    await refreshUnreadCount();
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={toggleOpen}
        aria-label="Notifications"
        className="relative rounded-full p-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-100"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {createPortal(
        <AnimatePresence>
          {isOpen && panelPosition && (
            <motion.div
              ref={panelRef}
              initial={{ opacity: 0, y: -8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              style={{ top: panelPosition.top, right: panelPosition.right }}
              className="popover-panel fixed z-[100] w-80 overflow-hidden rounded-2xl shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <h3 className="text-sm font-semibold text-slate-100">Notifications</h3>
                {items.some((n) => !n.is_read) && (
                  <button
                    onClick={handleMarkAllRead}
                    className="flex items-center gap-1 text-xs font-medium text-brand-cyan hover:underline"
                  >
                    <CheckCheck size={13} />
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-96 overflow-y-auto">
                {isLoading ? (
                  <p className="px-4 py-6 text-center text-sm text-slate-500">Loading…</p>
                ) : items.length === 0 ? (
                  <p className="px-4 py-6 text-center text-sm text-slate-500">No notifications yet.</p>
                ) : (
                  items.map((notification) => {
                    const Icon = NOTIFICATION_ICON[notification.type];
                    return (
                      <div
                        key={notification.id}
                        className={`flex gap-3 border-b border-white/10 px-4 py-3 last:border-0 ${
                          notification.is_read ? "opacity-60" : "bg-white/[0.03]"
                        }`}
                      >
                        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/5">
                          <Icon size={15} className="text-slate-300" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-slate-100">{notification.title}</p>
                          <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{notification.message}</p>
                          <p className="mt-1 text-[11px] text-slate-600">
                            {formatRelativeDate(notification.created_at)}
                          </p>
                        </div>
                        {!notification.is_read && (
                          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-cyan" />
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              <Link
                to="/dashboard/notifications"
                onClick={() => setIsOpen(false)}
                className="block border-t border-white/10 px-4 py-3 text-center text-xs font-medium text-brand-cyan hover:underline"
              >
                View all notifications
              </Link>
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}

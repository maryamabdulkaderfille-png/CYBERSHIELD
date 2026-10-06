import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as authService from "@/services/authService";

function initials(fullName: string): string {
  return fullName
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function DashboardTopbar({ onOpenSidebar }: { onOpenSidebar: () => void }) {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [isBannerDismissed, setIsBannerDismissed] = useState(false);
  const [isResending, setIsResending] = useState(false);

  if (!user) return null;

  const handleResend = async () => {
    setIsResending(true);
    try {
      await authService.resendVerification(user.email);
      showToast("Verification email sent — check your inbox.", "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not resend the verification email."), "error");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <header className="dashboard-chrome sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-white/5 bg-navy-900/70 px-4 py-4 backdrop-blur-xl sm:px-6">
      <button onClick={onOpenSidebar} className="text-slate-300 lg:hidden" aria-label="Open menu">
        <Menu size={22} />
      </button>

      <div className="hidden sm:block">
        {!user.is_verified && !isBannerDismissed && (
          <div className="flex items-center gap-2">
            <Badge variant="warning">Email not verified — check your inbox for a verification link</Badge>
            <button
              onClick={handleResend}
              disabled={isResending}
              className="text-xs font-medium text-brand-cyan hover:underline disabled:opacity-50"
            >
              {isResending ? "Sending…" : "Resend"}
            </button>
            <button
              onClick={() => setIsBannerDismissed(true)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        )}
      </div>

      <div className="ml-auto flex items-center gap-2">
        <NotificationBell />
        <Link to="/dashboard/profile" className="flex items-center gap-3 pl-1">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-slate-100">{user.full_name}</p>
            <p className="text-xs capitalize text-slate-500">{user.role}</p>
          </div>
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt=""
              className="h-9 w-9 shrink-0 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-blue to-brand-cyan text-xs font-bold text-navy-950">
              {initials(user.full_name)}
            </div>
          )}
        </Link>
      </div>
    </header>
  );
}

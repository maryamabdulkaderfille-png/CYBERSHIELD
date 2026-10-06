import { Activity, ArrowLeft, Ban, KeyRound, Mail, QrCode, ShieldCheck, ShieldOff, ShieldX, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { StatCard } from "@/components/dashboard/StatCard";
import { UnifiedScanList } from "@/components/scanCenter/UnifiedScanList";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as adminService from "@/services/adminService";
import type { AdminUserDetail, RestrictableFeature, UserRestrictionItem } from "@/types/admin";
import type { UserStatus } from "@/types/auth";

const STATUS_VARIANT: Record<UserStatus, "safe" | "warning" | "danger"> = {
  active: "safe",
  suspended: "warning",
  removed: "danger",
};

const RESTRICTION_LABELS: Record<RestrictableFeature, string> = {
  url: "URL Scanner",
  email: "Email Scanner",
  qr: "QR Scanner",
  reports: "Reports",
};

type PendingAction = { status: UserStatus; label: string; message: string } | null;

export function AdminUserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const { showToast } = useToast();
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [isSubmittingStatus, setIsSubmittingStatus] = useState(false);

  const [restrictions, setRestrictions] = useState<UserRestrictionItem[]>([]);
  const [isLoadingRestrictions, setIsLoadingRestrictions] = useState(true);
  const [pendingRestriction, setPendingRestriction] = useState<RestrictableFeature | null>(null);

  const load = () => {
    if (!userId) return;
    setIsLoading(true);
    adminService
      .getUserDetail(userId)
      .then(setDetail)
      .catch((err) => setError(extractErrorMessage(err, "Could not load this user.")))
      .finally(() => setIsLoading(false));
  };

  const loadRestrictions = () => {
    if (!userId) return;
    setIsLoadingRestrictions(true);
    adminService
      .listUserRestrictions(userId)
      .then(setRestrictions)
      .catch((err) => showToast(extractErrorMessage(err, "Could not load restrictions."), "error"))
      .finally(() => setIsLoadingRestrictions(false));
  };

  useEffect(load, [userId]);
  useEffect(loadRestrictions, [userId]);

  const runStatusChange = async () => {
    if (!userId || !pendingAction) return;
    setIsSubmittingStatus(true);
    try {
      await adminService.setUserStatus(userId, pendingAction.status);
      showToast(`User ${pendingAction.label.toLowerCase()}.`, "success");
      setPendingAction(null);
      load();
    } catch (err) {
      showToast(extractErrorMessage(err, `Could not ${pendingAction.label.toLowerCase()} this user.`), "error");
    } finally {
      setIsSubmittingStatus(false);
    }
  };

  const toggleRestriction = async (feature: RestrictableFeature, currentlyRestricted: boolean) => {
    if (!userId) return;
    setPendingRestriction(feature);
    try {
      if (currentlyRestricted) {
        await adminService.removeUserRestriction(userId, feature);
        showToast(`${RESTRICTION_LABELS[feature]} access restored.`, "success");
      } else {
        await adminService.addUserRestriction(userId, feature);
        showToast(`${RESTRICTION_LABELS[feature]} restricted.`, "success");
      }
      loadRestrictions();
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not update this restriction."), "error");
    } finally {
      setPendingRestriction(null);
    }
  };

  const handleResetPassword = async () => {
    if (!userId) return;
    try {
      await adminService.resetUserPassword(userId);
    } catch (err) {
      showToast(extractErrorMessage(err, "Admin password reset is coming in a future update."), "info");
    }
  };

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (error || !detail) {
    return <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error ?? "User not found."}</div>;
  }

  const { user, stats, sessions } = detail;

  return (
    <div className="flex flex-col gap-6">
      <Link to="/admin/users" className="flex w-fit items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200">
        <ArrowLeft size={14} />
        Back to Users
      </Link>

      <div className="glass-card flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-50">{user.full_name}</h1>
          <p className="text-sm text-slate-500">
            @{user.username} · {user.email}
          </p>
          <div className="mt-2 flex gap-2">
            <Badge variant={user.role === "admin" ? "danger" : "neutral"}>{user.role}</Badge>
            <Badge variant={STATUS_VARIANT[user.status]}>
              {user.status[0].toUpperCase() + user.status.slice(1)}
            </Badge>
            <Badge variant={user.is_verified ? "safe" : "warning"}>{user.is_verified ? "Verified" : "Unverified"}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {user.status !== "active" && (
            <button
              onClick={() =>
                setPendingAction({
                  status: "active",
                  label: "Reactivated",
                  message: `Reactivate ${user.full_name}? They will be able to log in again immediately.`,
                })
              }
              className="btn-secondary border-safe/30 text-safe"
            >
              <ShieldCheck size={16} />
              Reactivate
            </button>
          )}
          {user.status !== "suspended" && user.status !== "removed" && (
            <button
              onClick={() =>
                setPendingAction({
                  status: "suspended",
                  label: "Suspended",
                  message: `Suspend ${user.full_name}? Their sessions will be revoked immediately and they won't be able to log in until reactivated.`,
                })
              }
              className="btn-secondary border-warning/30 text-warning"
            >
              <ShieldOff size={16} />
              Suspend
            </button>
          )}
          {user.status !== "removed" && (
            <button
              onClick={() =>
                setPendingAction({
                  status: "removed",
                  label: "Removed",
                  message: `Remove ${user.full_name}? This is a soft delete — their scan history and audit trail are kept, but they're hidden from the default user list and can't log in. This can be undone with Reactivate.`,
                })
              }
              className="btn-secondary border-danger/30 text-danger"
            >
              <Trash2 size={16} />
              Remove
            </button>
          )}
          <button onClick={handleResetPassword} className="btn-secondary">
            <KeyRound size={16} />
            Reset Password
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={pendingAction !== null}
        title={`${pendingAction?.label ?? ""} account?`}
        message={pendingAction?.message ?? ""}
        confirmLabel={pendingAction?.label ?? "Confirm"}
        isDangerous={pendingAction?.status !== "active"}
        isSubmitting={isSubmittingStatus}
        onConfirm={runStatusChange}
        onCancel={() => setPendingAction(null)}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Activity} label="Total Scans" value={String(stats.total_scans)} accent="blue" />
        <StatCard icon={ShieldCheck} label="Safe Scans" value={String(stats.safe_scans)} accent="safe" />
        <StatCard icon={ShieldX} label="Dangerous Scans" value={String(stats.dangerous_scans)} accent="danger" />
        <StatCard icon={Mail} label="Email Scans" value={String(stats.email_scans)} accent="cyan" />
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-1 flex items-center gap-2 text-base font-semibold text-slate-100">
          <Ban size={16} className="text-slate-400" />
          Feature Restrictions
        </h2>
        <p className="mb-4 text-sm text-slate-500">
          Block this user from specific parts of the system. Enforced server-side on every relevant request, not
          just hidden in the UI.
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {(Object.keys(RESTRICTION_LABELS) as RestrictableFeature[]).map((feature) => {
            const restricted = restrictions.some((r) => r.feature === feature);
            return (
              <div
                key={feature}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-200">{RESTRICTION_LABELS[feature]}</p>
                  <p className="text-xs text-slate-500">{restricted ? "Restricted" : "Allowed"}</p>
                </div>
                <button
                  onClick={() => toggleRestriction(feature, restricted)}
                  disabled={isLoadingRestrictions || pendingRestriction === feature}
                  role="switch"
                  aria-checked={restricted}
                  aria-label={`Toggle ${RESTRICTION_LABELS[feature]} restriction`}
                  className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50 ${
                    restricted ? "bg-danger" : "bg-white/10"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                      restricted ? "translate-x-5" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-100">Active Sessions</h2>
        {sessions.length === 0 ? (
          <p className="text-sm text-slate-500">No active sessions.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-white/5">
            {sessions.map((session) => (
              <li key={session.id} className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0 text-sm">
                <span className="text-slate-300">{session.user_agent ?? "Unknown device"}</span>
                <span className="text-xs text-slate-500">{session.ip_address ?? "Unknown IP"}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-100">Recent Activity</h2>
        <UnifiedScanList
          items={stats.recent_activity}
          emptyIcon={QrCode}
          emptyTitle="No activity yet"
          emptyDescription="This user hasn't run any scans yet."
        />
      </div>
    </div>
  );
}

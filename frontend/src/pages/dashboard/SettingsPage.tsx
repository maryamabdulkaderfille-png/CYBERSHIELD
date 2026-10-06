import {
  AlertTriangle,
  Ban,
  Bell,
  Calendar,
  Download,
  Eye,
  EyeOff,
  Globe,
  Laptop,
  Loader2,
  Mail,
  MessageCircleQuestion,
  Moon,
  Shield,
  ShieldAlert,
  ShieldBan,
  Smartphone,
  Sun,
  Trash2,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Select } from "@/components/common/Select";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import { applyTheme } from "@/lib/theme";
import * as settingsService from "@/services/settingsService";
import type { ProtectionMode } from "@/types/protection";
import type { Session, Theme, UserSettings } from "@/types/settings";

// A hand-picked fallback for browsers without Intl.supportedValuesOf (older
// Safari) — the primary source below covers the complete IANA database.
const FALLBACK_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Sao_Paulo",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Moscow",
  "Africa/Cairo",
  "Africa/Lagos",
  "Africa/Nairobi",
  "Asia/Dubai",
  "Asia/Karachi",
  "Asia/Kolkata",
  "Asia/Dhaka",
  "Asia/Bangkok",
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
  "Pacific/Auckland",
];

// tsconfig targets ES2020, which predates supportedValuesOf's TS lib types —
// this local type covers the runtime check without widening the project's lib.
type IntlWithSupportedValuesOf = typeof Intl & {
  supportedValuesOf?: (key: "timeZone") => string[];
};

function getAllTimezones(): string[] {
  const intl = Intl as IntlWithSupportedValuesOf;
  if (typeof intl.supportedValuesOf === "function") {
    try {
      return intl.supportedValuesOf("timeZone");
    } catch {
      return FALLBACK_TIMEZONES;
    }
  }
  return FALLBACK_TIMEZONES;
}

// The backend accepts any zoneinfo IANA timezone name — this mirrors that
// completeness on the frontend instead of a short curated subset.
const TIMEZONES = getAllTimezones();

const LANGUAGES: { code: string; label: string }[] = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "it", label: "Italiano" },
  { code: "pt", label: "Português" },
  { code: "nl", label: "Nederlands" },
  { code: "sv", label: "Svenska" },
  { code: "no", label: "Norsk" },
  { code: "da", label: "Dansk" },
  { code: "fi", label: "Suomi" },
  { code: "pl", label: "Polski" },
  { code: "cs", label: "Čeština" },
  { code: "ro", label: "Română" },
  { code: "hu", label: "Magyar" },
  { code: "el", label: "Ελληνικά" },
  { code: "tr", label: "Türkçe" },
  { code: "ru", label: "Русский" },
  { code: "uk", label: "Українська" },
  { code: "ar", label: "العربية" },
  { code: "he", label: "עברית" },
  { code: "fa", label: "فارسی" },
  { code: "ur", label: "اردو" },
  { code: "so", label: "Soomaali" },
  { code: "sw", label: "Kiswahili" },
  { code: "am", label: "አማርኛ" },
  { code: "ha", label: "Hausa" },
  { code: "hi", label: "हिन्दी" },
  { code: "bn", label: "বাংলা" },
  { code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "th", label: "ไทย" },
  { code: "vi", label: "Tiếng Việt" },
  { code: "id", label: "Bahasa Indonesia" },
  { code: "ms", label: "Bahasa Melayu" },
  { code: "zh", label: "中文" },
  { code: "ja", label: "日本語" },
  { code: "ko", label: "한국어" },
];

const THEME_OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "dark", label: "Dark", icon: Moon },
  { value: "light", label: "Light", icon: Sun },
  { value: "system", label: "System", icon: Laptop },
];

const PROTECTION_MODE_OPTIONS: { value: ProtectionMode; label: string; description: string; icon: typeof Shield }[] = [
  {
    value: "warn_only",
    label: "Warn Only",
    description: "Show a dismissible warning on Dangerous sites (the extension's default behavior).",
    icon: MessageCircleQuestion,
  },
  {
    value: "ask_before_blocking",
    label: "Ask Before Blocking",
    description: "The warning prompts you to block the site, rather than blocking automatically.",
    icon: ShieldAlert,
  },
  {
    value: "auto_block_dangerous",
    label: "Automatically Block Dangerous Websites",
    description: "Dangerous sites are added to your Block List automatically — no click required.",
    icon: Ban,
  },
  {
    value: "auto_block_dangerous_suspicious",
    label: "Automatically Block Dangerous + Suspicious Websites",
    description: "The strictest mode — also auto-blocks Suspicious sites, not just Dangerous ones.",
    icon: ShieldBan,
  },
];

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();

  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    settingsService
      .getSettings()
      .then((loaded) => {
        setSettings(loaded);
        applyTheme(loaded.theme);
      })
      .catch((err) => showToast(extractErrorMessage(err, "Could not load your settings."), "error"))
      .finally(() => setIsLoadingSettings(false));

    settingsService
      .getSessions()
      .then(setSessions)
      .catch(() => undefined)
      .finally(() => setIsLoadingSessions(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!user) return null;

  const applySettingChange = async (patch: Partial<UserSettings>) => {
    if (!settings) return;
    const previous = settings;
    setSettings({ ...settings, ...patch });
    if (patch.theme) applyTheme(patch.theme);
    setIsSavingSettings(true);
    try {
      const updated = await settingsService.updateSettings(patch);
      setSettings(updated);
    } catch (err) {
      setSettings(previous);
      if (patch.theme) applyTheme(previous.theme);
      showToast(extractErrorMessage(err, "Could not update settings."), "error");
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    try {
      await settingsService.revokeSession(sessionId);
      setSessions((current) => current.filter((s) => s.id !== sessionId));
      showToast("Session revoked.", "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not revoke that session."), "error");
    }
  };

  const handleRevokeOthers = async () => {
    try {
      const count = await settingsService.revokeOtherSessions();
      setSessions((current) => current.filter((s) => s.is_current));
      showToast(`${count} other session(s) revoked.`, "success");
    } catch (err) {
      showToast(extractErrorMessage(err, "Could not revoke other sessions."), "error");
    }
  };

  const handleExportData = async () => {
    try {
      await settingsService.exportMyData();
    } catch (err) {
      showToast(extractErrorMessage(err, "Data export is coming in a future update."), "info");
    }
  };

  const handleDeactivate = async (event: FormEvent) => {
    event.preventDefault();
    setDeleteError(null);
    setIsDeleting(true);
    try {
      await settingsService.deactivateAccount(deletePassword);
      showToast("Your account has been deactivated.", "info");
      await logout();
    } catch (err) {
      setDeleteError(extractErrorMessage(err, "Could not deactivate your account."));
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">Settings</h1>
        <p className="mt-1 text-sm text-slate-400">Account settings and preferences.</p>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-5 text-base font-semibold text-slate-100">Account information</h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex items-center gap-3">
            <Mail size={16} className="text-slate-500" />
            <div>
              <dt className="text-xs text-slate-500">Email</dt>
              <dd className="text-sm text-slate-200">{user.email}</dd>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Calendar size={16} className="text-slate-500" />
            <div>
              <dt className="text-xs text-slate-500">Member since</dt>
              <dd className="text-sm text-slate-200">{formatDate(user.created_at)}</dd>
            </div>
          </div>
        </dl>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-5 flex items-center gap-2 text-base font-semibold text-slate-100">
          <Sun size={16} className="text-slate-400" />
          Appearance & language
        </h2>

        {isLoadingSettings || !settings ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <div className="flex flex-col gap-5">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Theme</p>
              <div className="flex gap-2">
                {THEME_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => applySettingChange({ theme: option.value })}
                    className={`flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition-colors ${
                      settings.theme === option.value
                        ? "border-brand-cyan/50 bg-brand-cyan/10 text-brand-cyan"
                        : "border-white/10 bg-white/[0.03] text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <option.icon size={15} />
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-300">Language</label>
                <Select
                  value={settings.language}
                  onChange={(value) => applySettingChange({ language: value })}
                  options={LANGUAGES.map((lang) => ({ value: lang.code, label: lang.label }))}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-300">Time zone</label>
                <Select
                  value={settings.timezone}
                  onChange={(value) => applySettingChange({ timezone: value })}
                  options={(TIMEZONES.includes(settings.timezone)
                    ? TIMEZONES
                    : [settings.timezone, ...TIMEZONES]
                  ).map((tz) => ({ value: tz, label: tz }))}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <div className="mb-5 flex items-center gap-2">
          <Bell size={16} className="text-slate-400" />
          <h2 className="text-base font-semibold text-slate-100">Notification preferences</h2>
        </div>

        {isLoadingSettings || !settings ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <div className="flex flex-col divide-y divide-white/5">
            {(
              [
                { key: "notify_high_risk_url", label: "High risk URL detected" },
                { key: "notify_dangerous_email", label: "Dangerous email detected" },
                { key: "notify_qr_threat", label: "QR code threat detected" },
                { key: "notify_weekly_summary", label: "Weekly security summary" },
              ] as const
            ).map((row) => (
              <label key={row.key} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <span className="text-sm text-slate-300">{row.label}</span>
                <input
                  type="checkbox"
                  checked={settings[row.key]}
                  onChange={(e) => applySettingChange({ [row.key]: e.target.checked })}
                  className="h-5 w-9 shrink-0 cursor-pointer appearance-none rounded-full bg-white/10 transition-colors checked:bg-brand-cyan relative before:absolute before:left-0.5 before:top-0.5 before:h-4 before:w-4 before:rounded-full before:bg-white before:transition-transform checked:before:translate-x-4"
                />
              </label>
            ))}
          </div>
        )}
        {isSavingSettings && (
          <p className="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
            <Loader2 size={12} className="animate-spin" /> Saving…
          </p>
        )}
      </div>

      <div className="glass-card p-6">
        <div className="mb-5 flex items-center gap-2">
          <ShieldBan size={16} className="text-slate-400" />
          <h2 className="text-base font-semibold text-slate-100">Active Protection</h2>
        </div>
        <p className="mb-4 text-sm text-slate-500">
          Controls how the CyberShield browser extension reacts to a Dangerous (or Suspicious) site. Changes apply
          immediately — no save button needed.
        </p>

        {isLoadingSettings || !settings ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <div className="flex flex-col gap-2">
            {PROTECTION_MODE_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => applySettingChange({ protection_mode: option.value })}
                className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                  settings.protection_mode === option.value
                    ? "border-brand-cyan/50 bg-brand-cyan/10"
                    : "border-white/10 bg-white/[0.03] hover:border-white/20"
                }`}
              >
                <span
                  className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                    settings.protection_mode === option.value ? "bg-brand-cyan/20 text-brand-cyan" : "bg-white/5 text-slate-400"
                  }`}
                >
                  <option.icon size={16} aria-hidden="true" />
                </span>
                <span>
                  <span
                    className={`block text-sm font-semibold ${
                      settings.protection_mode === option.value ? "text-brand-cyan" : "text-slate-200"
                    }`}
                  >
                    {option.label}
                  </span>
                  <span className="block text-xs text-slate-500">{option.description}</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-slate-400" />
            <h2 className="text-base font-semibold text-slate-100">Privacy</h2>
          </div>
        </div>
        {isLoadingSettings || !settings ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <label className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm text-slate-300">Profile visibility</p>
              <p className="text-xs text-slate-500">Whether other CyberShield users can see your profile.</p>
            </div>
            <Select
              className="w-36"
              value={settings.profile_visibility}
              onChange={(value) =>
                applySettingChange({ profile_visibility: value as UserSettings["profile_visibility"] })
              }
              options={[
                { value: "private", label: "Private" },
                { value: "public", label: "Public" },
              ]}
            />
          </label>
        )}
      </div>

      <div className="glass-card p-6">
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Smartphone size={16} className="text-slate-400" />
            <h2 className="text-base font-semibold text-slate-100">Active sessions</h2>
          </div>
          {sessions.length > 1 && (
            <button onClick={handleRevokeOthers} className="text-xs font-medium text-brand-cyan hover:underline">
              Log out other sessions
            </button>
          )}
        </div>

        {isLoadingSessions ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : sessions.length === 0 ? (
          <p className="text-sm text-slate-500">No active sessions found.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-white/5">
            {sessions.map((session) => (
              <li key={session.id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 truncate text-sm text-slate-200">
                    {session.user_agent ?? "Unknown device"}
                    {session.is_current && (
                      <span className="rounded-full bg-brand-cyan/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-cyan">
                        This device
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500">
                    {session.ip_address ?? "Unknown IP"} · Last active {formatDateTime(session.last_seen_at)}
                  </p>
                </div>
                {!session.is_current && (
                  <button
                    onClick={() => handleRevokeSession(session.id)}
                    className="shrink-0 text-xs font-medium text-danger hover:underline"
                  >
                    Revoke
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="glass-card p-6">
        <div className="mb-2 flex items-center gap-2">
          <Download size={16} className="text-slate-400" />
          <h2 className="text-base font-semibold text-slate-100">Export my data</h2>
        </div>
        <p className="mb-4 text-sm text-slate-500">
          Download a copy of your account data, scan history, and reports.
        </p>
        <button onClick={handleExportData} className="btn-secondary">
          <Download size={16} />
          Request export
        </button>
      </div>

      <div className="glass-card border-danger/20 p-6">
        <div className="mb-2 flex items-center gap-2 text-danger">
          <AlertTriangle size={18} />
          <h2 className="text-base font-semibold">Danger zone</h2>
        </div>
        <p className="mb-4 text-sm text-slate-500">
          Deactivating your account disables sign-in and ends every active session immediately. This can be
          reversed by contacting support.
        </p>

        {!showDeleteConfirm ? (
          <button onClick={() => setShowDeleteConfirm(true)} className="btn-secondary border-danger/30 text-danger">
            <Trash2 size={16} />
            Deactivate account
          </button>
        ) : (
          <form onSubmit={handleDeactivate} className="flex flex-col gap-4 sm:max-w-sm">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-slate-300">Confirm your password</label>
              <div className="relative">
                <input
                  type={showDeletePassword ? "text" : "password"}
                  className="input-field pr-10"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowDeletePassword((prev) => !prev)}
                  className="absolute inset-y-0 right-3 flex items-center text-slate-500 hover:text-slate-300"
                >
                  {showDeletePassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            {deleteError && (
              <p className="flex items-center gap-1.5 text-sm text-danger">
                <ShieldAlert size={14} /> {deleteError}
              </p>
            )}
            <div className="flex gap-2">
              <button type="submit" disabled={isDeleting} className="btn-secondary border-danger/30 text-danger">
                {isDeleting ? "Deactivating…" : "Confirm deactivation"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeletePassword("");
                  setDeleteError(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="glass-card p-6 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <Globe size={13} />
          Theme, language, and timezone preferences are saved to your account and are applied throughout
          CyberShield.
        </div>
      </div>
    </div>
  );
}

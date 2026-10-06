import { Activity, Eye, EyeOff, FileText, KeyRound, Mail, QrCode, Save, Shield, ShieldCheck, ShieldX } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Badge } from "@/components/common/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { StatCard } from "@/components/dashboard/StatCard";
import { UnifiedScanList } from "@/components/scanCenter/UnifiedScanList";
import { FormField } from "@/components/forms/FormField";
import { PasswordStrengthMeter } from "@/components/forms/PasswordStrengthMeter";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as authService from "@/services/authService";
import * as profileService from "@/services/profileService";
import type { ProfileStats } from "@/types/profile";

function initials(fullName: string): string {
  return fullName
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const { showToast } = useToast();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [username, setUsername] = useState(user?.username ?? "");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [phone, setPhone] = useState(user?.phone ?? "");
  const [country, setCountry] = useState(user?.country ?? "");
  const [bio, setBio] = useState(user?.bio ?? "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? "");
  const [isSavingExtended, setIsSavingExtended] = useState(false);
  const [extendedError, setExtendedError] = useState<string | null>(null);

  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    profileService
      .getProfile()
      .then((response) => setStats(response.stats))
      .catch((err) => setStatsError(extractErrorMessage(err, "Could not load your profile stats.")))
      .finally(() => setIsLoadingStats(false));
  }, []);

  if (!user) return null;

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setProfileError(null);
    setIsSavingProfile(true);
    try {
      const updated = await authService.updateProfile({ full_name: fullName, username });
      setUser(updated);
      showToast("Profile updated.", "success");
    } catch (err) {
      setProfileError(extractErrorMessage(err, "Could not update your profile."));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleExtendedSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setExtendedError(null);
    setIsSavingExtended(true);
    try {
      const updated = await profileService.updateExtendedProfile({
        phone: phone || undefined,
        country: country || undefined,
        bio: bio || undefined,
        avatar_url: avatarUrl || undefined,
      });
      setUser(updated);
      showToast("Profile details updated.", "success");
    } catch (err) {
      setExtendedError(extractErrorMessage(err, "Could not update your profile details."));
    } finally {
      setIsSavingExtended(false);
    }
  };

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setPasswordError(null);

    if (newPassword !== confirmNewPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    setIsChangingPassword(true);
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      showToast("Password updated.", "success");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err) {
      setPasswordError(extractErrorMessage(err, "Could not update your password."));
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">Profile</h1>
        <p className="mt-1 text-sm text-slate-400">Manage your account details and security.</p>
      </div>

      <div className="glass-card flex flex-col items-center gap-4 p-6 sm:flex-row">
        {user.avatar_url ? (
          <img src={user.avatar_url} alt="" className="h-16 w-16 shrink-0 rounded-full object-cover" />
        ) : (
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-blue to-brand-cyan text-lg font-bold text-navy-950">
            {initials(user.full_name)}
          </div>
        )}
        <div className="min-w-0 flex-1 text-center sm:text-left">
          <p className="truncate text-lg font-semibold text-slate-100">{user.full_name}</p>
          <p className="truncate text-sm text-slate-500">{user.email}</p>
          {user.bio && <p className="mt-1 max-w-md text-sm text-slate-400">{user.bio}</p>}
        </div>
        <div className="flex flex-col items-center gap-2 sm:items-end">
          <div className="flex gap-2">
            <Badge variant="brand">{user.role}</Badge>
            <Badge variant={user.is_verified ? "safe" : "warning"}>
              {user.is_verified ? "Verified" : "Unverified"}
            </Badge>
          </div>
          <p className="text-xs text-slate-500">
            Joined {formatDate(user.created_at)} · Last login {formatDate(user.last_login)}
          </p>
        </div>
      </div>

      {statsError && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{statsError}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Activity}
          label="Total Scans"
          value={isLoadingStats ? "—" : String(stats?.total_scans ?? 0)}
          accent="blue"
        />
        <StatCard
          icon={ShieldCheck}
          label="Safe Scans"
          value={isLoadingStats ? "—" : String(stats?.safe_scans ?? 0)}
          accent="safe"
        />
        <StatCard
          icon={ShieldX}
          label="Dangerous Scans"
          value={isLoadingStats ? "—" : String(stats?.dangerous_scans ?? 0)}
          accent="danger"
        />
        <StatCard
          icon={Shield}
          label="Security Score"
          value={isLoadingStats ? "—" : (stats?.security_score ?? "—").toString()}
          accent="cyan"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          icon={ShieldCheck}
          label="URL Scans"
          value={isLoadingStats ? "—" : String(stats?.url_scans ?? 0)}
          accent="blue"
        />
        <StatCard
          icon={Mail}
          label="Email Scans"
          value={isLoadingStats ? "—" : String(stats?.email_scans ?? 0)}
          accent="cyan"
        />
        <StatCard
          icon={QrCode}
          label="QR Scans"
          value={isLoadingStats ? "—" : String(stats?.qr_scans ?? 0)}
          accent="safe"
        />
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-100">
          <FileText size={16} className="text-slate-400" />
          Reports generated
        </h2>
        <p className="text-sm text-slate-400">
          {isLoadingStats
            ? "Loading…"
            : `${stats?.reports_generated ?? 0} report${stats?.reports_generated === 1 ? "" : "s"} available — every scan you run has a detailed report on demand.`}
        </p>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-100">Recent activity</h2>
        {isLoadingStats ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : stats && stats.recent_activity.length > 0 ? (
          <UnifiedScanList
            items={stats.recent_activity}
            emptyIcon={Activity}
            emptyTitle="No activity yet"
            emptyDescription="Your recent scans will show up here."
          />
        ) : (
          <EmptyState icon={Activity} title="No activity yet" description="Your recent scans will show up here." />
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-5 text-base font-semibold text-slate-100">Edit profile</h2>
        <form onSubmit={handleProfileSubmit} className="flex flex-col gap-5 sm:max-w-md">
          <FormField label="Full name" name="full_name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <FormField
            label="Username"
            name="username"
            required
            minLength={3}
            maxLength={32}
            pattern="[a-zA-Z0-9_]+"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          {profileError && <p className="text-sm text-danger">{profileError}</p>}
          <button type="submit" disabled={isSavingProfile} className="btn-primary self-start px-5 py-2.5">
            <Save size={16} />
            {isSavingProfile ? "Saving…" : "Save changes"}
          </button>
        </form>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-5 text-base font-semibold text-slate-100">Profile details</h2>
        <form onSubmit={handleExtendedSubmit} className="flex flex-col gap-5 sm:max-w-md">
          <FormField
            label="Phone"
            name="phone"
            placeholder="+1 555 123 4567"
            maxLength={32}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <FormField
            label="Country (ISO code)"
            name="country"
            placeholder="US"
            maxLength={2}
            value={country}
            onChange={(e) => setCountry(e.target.value.toUpperCase())}
          />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="bio" className="text-sm font-medium text-slate-300">
              Bio
            </label>
            <textarea
              id="bio"
              className="input-field min-h-[88px] resize-y"
              maxLength={500}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us a bit about yourself…"
            />
          </div>
          <FormField
            label="Avatar URL"
            name="avatar_url"
            type="url"
            placeholder="https://example.com/avatar.png"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
          />
          {extendedError && <p className="text-sm text-danger">{extendedError}</p>}
          <button type="submit" disabled={isSavingExtended} className="btn-primary self-start px-5 py-2.5">
            <Save size={16} />
            {isSavingExtended ? "Saving…" : "Save details"}
          </button>
        </form>
      </div>

      <div className="glass-card p-6">
        <h2 className="mb-5 text-base font-semibold text-slate-100">Change password</h2>
        <form onSubmit={handlePasswordSubmit} className="flex flex-col gap-5 sm:max-w-md">
          <FormField
            label="Current password"
            type={showPasswords ? "text" : "password"}
            name="current_password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            rightElement={
              <button type="button" onClick={() => setShowPasswords((prev) => !prev)} className="text-slate-500 hover:text-slate-300">
                {showPasswords ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />
          <div className="flex flex-col gap-2">
            <FormField
              label="New password"
              type={showPasswords ? "text" : "password"}
              name="new_password"
              autoComplete="new-password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <PasswordStrengthMeter password={newPassword} />
          </div>
          <FormField
            label="Confirm new password"
            type={showPasswords ? "text" : "password"}
            name="confirm_new_password"
            autoComplete="new-password"
            required
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
          />
          {passwordError && <p className="text-sm text-danger">{passwordError}</p>}
          <button type="submit" disabled={isChangingPassword} className="btn-primary self-start px-5 py-2.5">
            <KeyRound size={16} />
            {isChangingPassword ? "Updating…" : "Update password"}
          </button>
        </form>
      </div>
    </div>
  );
}

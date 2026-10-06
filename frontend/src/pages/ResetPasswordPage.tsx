import { Eye, EyeOff, KeyRound, ShieldAlert } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { FormField } from "@/components/forms/FormField";
import { PasswordStrengthMeter } from "@/components/forms/PasswordStrengthMeter";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as authService from "@/services/authService";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!token) {
    return (
      <div className="text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-danger/10">
          <ShieldAlert size={26} className="text-danger" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-slate-50">Invalid reset link</h1>
        <p className="mt-2 text-sm text-slate-400">
          This password reset link is missing its token. Please request a new one.
        </p>
        <Link to="/forgot-password" className="btn-primary mt-8 w-full py-3">
          Request new link
        </Link>
      </div>
    );
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await authService.resetPassword(token, password, confirmPassword);
      showToast("Password reset. You can now log in.", "success");
      navigate("/login", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "This reset link is invalid or has expired."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-50">Set a new password</h1>
      <p className="mt-2 text-sm text-slate-400">Choose a strong password you haven't used before.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <FormField
            label="New password"
            type={showPassword ? "text" : "password"}
            name="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            rightElement={
              <button type="button" onClick={() => setShowPassword((prev) => !prev)} className="text-slate-500 hover:text-slate-300">
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />
          <PasswordStrengthMeter password={password} />
        </div>

        <FormField
          label="Confirm new password"
          type={showPassword ? "text" : "password"}
          name="confirm_password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        {error && <p className="text-sm text-danger">{error}</p>}

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full py-3">
          <KeyRound size={18} />
          {isSubmitting ? "Resetting…" : "Reset password"}
        </button>
      </form>
    </div>
  );
}

import { Eye, EyeOff, LogIn } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { GoogleSignInButton } from "@/components/forms/GoogleSignInButton";
import { FormField } from "@/components/forms/FormField";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";

const GOOGLE_ERROR_MESSAGES: Record<string, string> = {
  google_failed: "Google Sign-In didn't complete. Please try again.",
  google_unverified_email: "That Google account's email isn't verified, so it can't be used to sign in.",
  account_deactivated: "This account has been deactivated.",
};

export function LoginPage() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const googleError = params.get("error");
    if (googleError) {
      setError(GOOGLE_ERROR_MESSAGES[googleError] ?? "Google Sign-In didn't complete. Please try again.");
    }
  }, [location.search]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password, remember_me: rememberMe });
      showToast("Welcome back!", "success");
      const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Invalid email or password."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-50">Welcome back</h1>
      <p className="mt-2 text-sm text-slate-400">Log in to access your CyberShield dashboard.</p>

      <div className="mt-8">
        <GoogleSignInButton label="Continue with Google" />
      </div>

      <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-600">
        <div className="h-px flex-1 bg-white/10" />
        or continue with email
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <FormField
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <FormField
          label="Password"
          type={showPassword ? "text" : "password"}
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          rightElement={
            <button type="button" onClick={() => setShowPassword((prev) => !prev)} className="text-slate-500 hover:text-slate-300">
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          }
        />

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-400">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-white/5 text-brand-cyan focus:ring-brand-cyan/40"
            />
            Remember me
          </label>
          <Link to="/forgot-password" className="text-brand-cyan hover:underline">
            Forgot password?
          </Link>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full py-3">
          <LogIn size={18} />
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-slate-400">
        Don't have an account?{" "}
        <Link to="/register" className="font-medium text-brand-cyan hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}

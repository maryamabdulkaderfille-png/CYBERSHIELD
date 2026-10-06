import { Eye, EyeOff, UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { FormField } from "@/components/forms/FormField";
import { GoogleSignInButton } from "@/components/forms/GoogleSignInButton";
import { PasswordStrengthMeter } from "@/components/forms/PasswordStrengthMeter";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";

export function RegisterPage() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        full_name: fullName,
        username,
        email,
        password,
        confirm_password: confirmPassword,
      });
      showToast("Account created! Check your email to verify your account.", "success");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Could not create your account."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-50">Create your account</h1>
      <p className="mt-2 text-sm text-slate-400">Start protecting yourself from phishing attacks in minutes.</p>

      <div className="mt-8">
        <GoogleSignInButton label="Sign up with Google" />
      </div>

      <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-600">
        <div className="h-px flex-1 bg-white/10" />
        or sign up with email
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <FormField
          label="Full name"
          name="full_name"
          autoComplete="name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />

        <FormField
          label="Username"
          name="username"
          autoComplete="username"
          required
          minLength={3}
          maxLength={32}
          pattern="[a-zA-Z0-9_]+"
          title="Letters, numbers, and underscores only"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <FormField
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <div className="flex flex-col gap-2">
          <FormField
            label="Password"
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
          label="Confirm password"
          type={showPassword ? "text" : "password"}
          name="confirm_password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        {error && <p className="text-sm text-danger">{error}</p>}

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full py-3">
          <UserPlus size={18} />
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-slate-400">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-brand-cyan hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

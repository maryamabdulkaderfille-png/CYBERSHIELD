import { Mail, MailCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { FormField } from "@/components/forms/FormField";
import * as authService from "@/services/authService";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await authService.forgotPassword(email);
    } finally {
      setIsSubmitting(false);
      setIsSubmitted(true);
    }
  };

  if (isSubmitted) {
    return (
      <div className="text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-safe/10">
          <MailCheck size={26} className="text-safe" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-slate-50">Check your inbox</h1>
        <p className="mt-2 text-sm text-slate-400">
          If an account exists for <span className="text-slate-200">{email}</span>, we've sent a password reset
          link. It expires in 30 minutes.
        </p>
        <Link to="/login" className="btn-secondary mt-8 w-full py-3">
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-50">Forgot your password?</h1>
      <p className="mt-2 text-sm text-slate-400">
        Enter the email associated with your account and we'll send you a reset link.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        <FormField
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <button type="submit" disabled={isSubmitting} className="btn-primary w-full py-3">
          <Mail size={18} />
          {isSubmitting ? "Sending…" : "Send reset link"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-slate-400">
        Remembered it?{" "}
        <Link to="/login" className="font-medium text-brand-cyan hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  );
}

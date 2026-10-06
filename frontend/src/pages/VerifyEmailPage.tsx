import { CheckCircle2, Loader2, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";
import { extractErrorMessage } from "@/lib/errors";
import * as authService from "@/services/authService";

type Status = "verifying" | "success" | "error";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const { refreshUser } = useAuth();

  const [status, setStatus] = useState<Status>("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("This verification link is missing its token.");
      return;
    }

    authService
      .verifyEmail(token)
      .then(async () => {
        setStatus("success");
        await refreshUser();
      })
      .catch((err) => {
        setStatus("error");
        setMessage(extractErrorMessage(err, "This verification link is invalid or has expired."));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="text-center">
      {status === "verifying" && (
        <>
          <Loader2 size={40} className="mx-auto animate-spin text-brand-cyan" />
          <h1 className="mt-4 text-2xl font-bold text-slate-50">Verifying your email…</h1>
        </>
      )}

      {status === "success" && (
        <>
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-safe/10">
            <CheckCircle2 size={26} className="text-safe" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-slate-50">Email verified</h1>
          <p className="mt-2 text-sm text-slate-400">Your account is now fully verified.</p>
          <Link to="/dashboard" className="btn-primary mt-8 w-full py-3">
            Go to dashboard
          </Link>
        </>
      )}

      {status === "error" && (
        <>
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-danger/10">
            <ShieldAlert size={26} className="text-danger" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-slate-50">Verification failed</h1>
          <p className="mt-2 text-sm text-slate-400">{message}</p>
          <Link to="/dashboard" className="btn-secondary mt-8 w-full py-3">
            Back to dashboard
          </Link>
        </>
      )}
    </div>
  );
}

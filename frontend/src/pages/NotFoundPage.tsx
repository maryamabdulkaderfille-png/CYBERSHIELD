import { ArrowLeft, ShieldQuestion } from "lucide-react";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/5">
        <ShieldQuestion size={30} className="text-slate-400" />
      </div>
      <h1 className="text-4xl font-extrabold text-slate-50">404</h1>
      <p className="max-w-sm text-slate-400">
        This page doesn't exist, or it may have moved. Let's get you back to safety.
      </p>
      <Link to="/" className="btn-primary">
        <ArrowLeft size={18} />
        Back to home
      </Link>
    </div>
  );
}

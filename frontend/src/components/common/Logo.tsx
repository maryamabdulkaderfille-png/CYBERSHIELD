import { ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

interface LogoProps {
  to?: string;
  size?: "sm" | "md" | "lg";
}

const SIZE_MAP = {
  sm: { icon: 18, text: "text-base" },
  md: { icon: 22, text: "text-lg" },
  lg: { icon: 30, text: "text-2xl" },
};

export function Logo({ to = "/", size = "md" }: LogoProps) {
  const { icon, text } = SIZE_MAP[size];
  return (
    <Link to={to} className="inline-flex items-center gap-2 font-bold tracking-tight">
      <span className="relative flex items-center justify-center rounded-lg bg-gradient-to-br from-brand-blue to-brand-cyan p-1.5 shadow-glow">
        <ShieldCheck size={icon} className="text-navy-950" strokeWidth={2.5} />
      </span>
      <span className={`${text} text-slate-50`}>
        Cyber<span className="brand-gradient-text">Shield</span>
      </span>
    </Link>
  );
}

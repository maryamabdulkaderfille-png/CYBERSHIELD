import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";

interface ComingSoonPageProps {
  icon: LucideIcon;
  title: string;
  description: string;
  phase: string;
}

export function ComingSoonPage({ icon, title, description, phase }: ComingSoonPageProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">{title}</h1>
        <p className="mt-1 text-sm text-slate-400">{description}</p>
      </div>
      <div className="glass-card p-6">
        <EmptyState
          icon={icon}
          title={`Coming in ${phase}`}
          description="This module is planned on the CyberShield roadmap and isn't available yet. Check back soon."
          action={
            <Link to="/dashboard" className="btn-secondary mt-2">
              Back to dashboard
            </Link>
          }
        />
      </div>
    </div>
  );
}

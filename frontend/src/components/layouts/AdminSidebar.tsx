import {
  ArrowLeft,
  Ban,
  FileClock,
  Gauge,
  LayoutGrid,
  ListChecks,
  LogOut,
  Radar,
  Shield,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { Logo } from "@/components/common/Logo";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { label: "System Overview", to: "/admin", icon: Gauge },
  { label: "Users", to: "/admin/users", icon: Users },
  { label: "Scans", to: "/admin/scans", icon: LayoutGrid },
  { label: "Blacklist", to: "/admin/blacklist", icon: Ban },
  { label: "Rules", to: "/admin/rules", icon: ListChecks },
  { label: "Threat Intelligence", to: "/admin/threat-intel", icon: Radar },
  { label: "Audit Logs", to: "/admin/audit-logs", icon: FileClock },
  { label: "System Health", to: "/admin/system", icon: Shield },
];

interface AdminSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AdminSidebar({ isOpen, onClose }: AdminSidebarProps) {
  const { logout } = useAuth();
  const { showToast } = useToast();

  const handleLogout = async () => {
    await logout();
    showToast("You've been logged out.", "info");
  };

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `sidebar-link ${isActive ? "bg-danger/10 text-danger hover:bg-danger/10 hover:text-danger" : ""}`;

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={onClose} aria-hidden="true" />}

      <aside
        className={`dashboard-chrome fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-white/5 bg-navy-950/95 backdrop-blur-xl transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <Logo to="/admin" />
          <button onClick={onClose} className="text-slate-400 lg:hidden" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <div className="mx-4 mb-2 rounded-lg bg-danger/10 px-3 py-1.5 text-center text-[11px] font-semibold uppercase tracking-wide text-danger">
          Admin Panel
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end className={linkClasses} onClick={onClose}>
              <item.icon size={18} />
              <span className="flex-1">{item.label}</span>
            </NavLink>
          ))}

          <div className="mt-6 border-t border-white/5 pt-4">
            <NavLink to="/dashboard" className="sidebar-link" onClick={onClose}>
              <ArrowLeft size={18} />
              Back to Dashboard
            </NavLink>
          </div>
        </nav>

        <div className="border-t border-white/5 p-3">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-slate-400 transition-colors hover:bg-danger/10 hover:text-danger"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}

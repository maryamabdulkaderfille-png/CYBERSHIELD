import {
  Ban,
  Bell,
  Globe2,
  LayoutDashboard,
  LayoutGrid,
  LogOut,
  Mail,
  QrCode,
  Settings,
  ShieldAlert,
  ShieldCheck,
  User,
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
  soon?: boolean;
}

const OVERVIEW_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Scan Center & History", to: "/dashboard/scan-center", icon: LayoutGrid },
];

const DETECTION_ITEMS: NavItem[] = [
  { label: "URL Scanner", to: "/dashboard/url-scanner", icon: ShieldCheck },
  { label: "Email Scanner", to: "/dashboard/email-scanner", icon: Mail },
  { label: "QR Scanner", to: "/dashboard/qr-scanner", icon: QrCode },
  { label: "Threat Intelligence", to: "/dashboard/threat-intelligence", icon: Globe2 },
];

const PROTECTION_ITEMS: NavItem[] = [{ label: "Blocked Websites", to: "/dashboard/protection/blocked", icon: Ban }];

const ACCOUNT_ITEMS: NavItem[] = [
  { label: "Notifications", to: "/dashboard/notifications", icon: Bell },
  { label: "Profile", to: "/dashboard/profile", icon: User },
  { label: "Settings", to: "/dashboard/settings", icon: Settings },
];

interface DashboardSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DashboardSidebar({ isOpen, onClose }: DashboardSidebarProps) {
  const { user, logout } = useAuth();
  const { showToast } = useToast();

  const handleLogout = async () => {
    await logout();
    showToast("You've been logged out.", "info");
  };

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `sidebar-link ${isActive ? "sidebar-link-active" : ""}`;

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={onClose} aria-hidden="true" />}

      <aside
        className={`dashboard-chrome fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-white/5 bg-navy-950/95 backdrop-blur-xl transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <Logo />
          <button onClick={onClose} className="text-slate-400 lg:hidden" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
          <p className="px-3.5 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Overview</p>
          {OVERVIEW_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end className={linkClasses} onClick={onClose}>
              <item.icon size={18} />
              <span className="flex-1">{item.label}</span>
              {item.soon && (
                <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Soon
                </span>
              )}
            </NavLink>
          ))}

          <div className="mt-6 border-t border-white/5 pt-4">
            <p className="px-3.5 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Detection</p>
            {DETECTION_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end className={linkClasses} onClick={onClose}>
                <item.icon size={18} />
                <span className="flex-1">{item.label}</span>
                {item.soon && (
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    Soon
                  </span>
                )}
              </NavLink>
            ))}
          </div>


          <div className="mt-6 border-t border-white/5 pt-4">
            <p className="px-3.5 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Protection</p>
            {PROTECTION_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} className={linkClasses} onClick={onClose}>
                <item.icon size={18} />
                <span className="flex-1">{item.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="mt-6 border-t border-white/5 pt-4">
            <p className="px-3.5 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Account</p>
            {ACCOUNT_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} className={linkClasses} onClick={onClose}>
                <item.icon size={18} />
                <span className="flex-1">{item.label}</span>
              </NavLink>
            ))}
          </div>

          {user?.role === "admin" && (
            <div className="mt-6 border-t border-white/5 pt-4">
              <p className="px-3.5 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
                Administration
              </p>
              <NavLink to="/admin" className={linkClasses} onClick={onClose}>
                <ShieldAlert size={18} />
                <span className="flex-1">Admin Panel</span>
              </NavLink>
            </div>
          )}
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

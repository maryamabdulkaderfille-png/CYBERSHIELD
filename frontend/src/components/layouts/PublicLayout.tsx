import { Outlet } from "react-router-dom";

import { PublicFooter } from "@/components/layouts/PublicFooter";
import { PublicNavbar } from "@/components/layouts/PublicNavbar";

export function PublicLayout() {
  return (
    // No hardcoded background here — body (index.css) already carries the
    // correct dark/light background per data-theme; a solid bg-[#05070d]
    // here used to sit on top of it and stay dark regardless of theme. The
    // public-shell class is what lets the light-theme text-color overrides
    // below reach this layout (previously they only covered the
    // authenticated app-shell/dashboard-chrome, leaving every public page
    // — including the landing page — entirely unthemed in light mode.
    <div className="public-shell flex min-h-screen flex-col text-slate-100">
      <PublicNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
}

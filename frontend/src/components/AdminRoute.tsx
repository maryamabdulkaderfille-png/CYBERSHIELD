import { Navigate, Outlet } from "react-router-dom";

import { LoadingScreen } from "@/components/common/LoadingScreen";
import { useAuth } from "@/context/AuthContext";

/** Sits *inside* ProtectedRoute (already-authenticated) — this only adds
 * the role check. A non-admin hitting /admin/* is redirected to the
 * regular dashboard rather than shown a 404, since the route legitimately
 * exists for admins; it's an authorization boundary, not a missing page. */
export function AdminRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <LoadingScreen />;
  if (user?.role !== "admin") return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}

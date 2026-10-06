import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AdminRoute } from "@/components/AdminRoute";
import { LoadingScreen } from "@/components/common/LoadingScreen";
import { GuestRoute } from "@/components/GuestRoute";
import { AdminLayout } from "@/components/layouts/AdminLayout";
import { AuthLayout } from "@/components/layouts/AuthLayout";
import { DashboardLayout } from "@/components/layouts/DashboardLayout";
import { PublicLayout } from "@/components/layouts/PublicLayout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { QuickScanEmailPage } from "@/pages/QuickScanEmailPage";
import { QuickScanPage } from "@/pages/QuickScanPage";
import { QuickScanQrPage } from "@/pages/QuickScanQrPage";
import { QuickScanUrlPage } from "@/pages/QuickScanUrlPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { VerifyEmailPage } from "@/pages/VerifyEmailPage";

// Dashboard/admin pages are only ever reached after login, so they're
// code-split out of the initial (public-facing) bundle rather than eagerly
// imported — the landing page and auth flows never pay for their weight.
const AdminAuditLogsPage = lazy(() => import("@/pages/admin/AdminAuditLogsPage").then((m) => ({ default: m.AdminAuditLogsPage })));
const AdminBlacklistPage = lazy(() => import("@/pages/admin/AdminBlacklistPage").then((m) => ({ default: m.AdminBlacklistPage })));
const AdminOverviewPage = lazy(() => import("@/pages/admin/AdminOverviewPage").then((m) => ({ default: m.AdminOverviewPage })));
const AdminRulesPage = lazy(() => import("@/pages/admin/AdminRulesPage").then((m) => ({ default: m.AdminRulesPage })));
const AdminScansPage = lazy(() => import("@/pages/admin/AdminScansPage").then((m) => ({ default: m.AdminScansPage })));
const AdminSystemHealthPage = lazy(() => import("@/pages/admin/AdminSystemHealthPage").then((m) => ({ default: m.AdminSystemHealthPage })));
const AdminThreatIntelPage = lazy(() => import("@/pages/admin/AdminThreatIntelPage").then((m) => ({ default: m.AdminThreatIntelPage })));
const AdminUserDetailPage = lazy(() => import("@/pages/admin/AdminUserDetailPage").then((m) => ({ default: m.AdminUserDetailPage })));
const AdminUsersPage = lazy(() => import("@/pages/admin/AdminUsersPage").then((m) => ({ default: m.AdminUsersPage })));

const BlockedWebsitesPage = lazy(() => import("@/pages/dashboard/BlockedWebsitesPage").then((m) => ({ default: m.BlockedWebsitesPage })));
const DashboardHomePage = lazy(() => import("@/pages/dashboard/DashboardHomePage").then((m) => ({ default: m.DashboardHomePage })));
const EmailScannerPage = lazy(() => import("@/pages/dashboard/EmailScannerPage").then((m) => ({ default: m.EmailScannerPage })));
const NotificationsPage = lazy(() => import("@/pages/dashboard/NotificationsPage").then((m) => ({ default: m.NotificationsPage })));
const ProfilePage = lazy(() => import("@/pages/dashboard/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const QrScannerPage = lazy(() => import("@/pages/dashboard/QrScannerPage").then((m) => ({ default: m.QrScannerPage })));
const ReportPage = lazy(() => import("@/pages/dashboard/ReportPage").then((m) => ({ default: m.ReportPage })));
const ScanCenterPage = lazy(() => import("@/pages/dashboard/ScanCenterPage").then((m) => ({ default: m.ScanCenterPage })));
const SettingsPage = lazy(() => import("@/pages/dashboard/SettingsPage").then((m) => ({ default: m.SettingsPage })));
const ThreatIntelligencePage = lazy(() => import("@/pages/dashboard/ThreatIntelligencePage").then((m) => ({ default: m.ThreatIntelligencePage })));
const UrlScannerPage = lazy(() => import("@/pages/dashboard/UrlScannerPage").then((m) => ({ default: m.UrlScannerPage })));

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
        <Route path="/terms-of-service" element={<TermsOfServicePage />} />
        <Route path="/quick-scan" element={<QuickScanPage />} />
        <Route path="/quick-scan/url" element={<QuickScanUrlPage />} />
        <Route path="/quick-scan/email" element={<QuickScanEmailPage />} />
        <Route path="/quick-scan/qr" element={<QuickScanQrPage />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        </Route>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route
          element={
            <Suspense fallback={<LoadingScreen label="Loading…" />}>
              <DashboardLayout />
            </Suspense>
          }
        >
          <Route path="/dashboard" element={<DashboardHomePage />} />
          <Route path="/dashboard/profile" element={<ProfilePage />} />
          <Route path="/dashboard/settings" element={<SettingsPage />} />
          <Route path="/dashboard/url-scanner" element={<UrlScannerPage />} />
          <Route path="/dashboard/history" element={<Navigate to="/dashboard/scan-center" replace />} />
          <Route path="/dashboard/email-scanner" element={<EmailScannerPage />} />
          <Route path="/dashboard/qr-scanner" element={<QrScannerPage />} />
          <Route path="/dashboard/scan-center" element={<ScanCenterPage />} />
          <Route path="/dashboard/threat-intelligence" element={<ThreatIntelligencePage />} />
          <Route path="/dashboard/notifications" element={<NotificationsPage />} />
          <Route path="/dashboard/protection/blocked" element={<BlockedWebsitesPage />} />
          <Route path="/dashboard/reports/:scannerType/:scanId" element={<ReportPage />} />
          <Route path="/dashboard/reports" element={<Navigate to="/dashboard/scan-center" replace />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AdminRoute />}>
          <Route
            element={
              <Suspense fallback={<LoadingScreen label="Loading…" />}>
                <AdminLayout />
              </Suspense>
            }
          >
            <Route path="/admin" element={<AdminOverviewPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/users/:userId" element={<AdminUserDetailPage />} />
            <Route path="/admin/scans" element={<AdminScansPage />} />
            <Route path="/admin/blacklist" element={<AdminBlacklistPage />} />
            <Route path="/admin/rules" element={<AdminRulesPage />} />
            <Route path="/admin/audit-logs" element={<AdminAuditLogsPage />} />
            <Route path="/admin/system" element={<AdminSystemHealthPage />} />
            <Route path="/admin/threat-intel" element={<AdminThreatIntelPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}

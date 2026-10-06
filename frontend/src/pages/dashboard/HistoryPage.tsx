import { useSearchParams } from "react-router-dom";

import { EmailHistoryPage } from "@/pages/dashboard/EmailHistoryPage";
import { ScanHistoryPage } from "@/pages/dashboard/ScanHistoryPage";

type HistoryTab = "url" | "email";

export function HistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab: HistoryTab = searchParams.get("tab") === "email" ? "email" : "url";

  const setActiveTab = (tab: HistoryTab) => {
    setSearchParams(tab === "url" ? {} : { tab });
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab("url")}
          className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
            activeTab === "url" ? "bg-brand-cyan/10 text-brand-cyan" : "text-slate-500 hover:text-slate-300"
          }`}
        >
          URL Scans
        </button>
        <button
          onClick={() => setActiveTab("email")}
          className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
            activeTab === "email" ? "bg-brand-cyan/10 text-brand-cyan" : "text-slate-500 hover:text-slate-300"
          }`}
        >
          Email Scans
        </button>
      </div>

      {activeTab === "url" ? <ScanHistoryPage /> : <EmailHistoryPage />}
    </div>
  );
}

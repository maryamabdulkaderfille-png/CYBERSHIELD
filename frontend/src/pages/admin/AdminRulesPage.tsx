import { ListChecks } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/common/Badge";
import { useToast } from "@/context/ToastContext";
import { extractErrorMessage } from "@/lib/errors";
import * as adminService from "@/services/adminService";
import type { DetectionRule, RuleCategory } from "@/types/admin";

const SEVERITY_VARIANT: Record<string, "safe" | "warning" | "danger" | "neutral" | "brand"> = {
  info: "neutral",
  low: "brand",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

function RuleTable({
  title,
  rules,
  onToggle,
}: {
  title: string;
  rules: DetectionRule[];
  onToggle: (rule: DetectionRule) => void;
}) {
  return (
    <div className="glass-card p-6">
      <h2 className="mb-4 text-base font-semibold text-slate-100">{title}</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
              <th className="pb-3 pr-4 font-medium">Rule</th>
              <th className="pb-3 pr-4 font-medium">Description</th>
              <th className="pb-3 pr-4 font-medium">Severity</th>
              <th className="pb-3 pr-4 font-medium">Version</th>
              <th className="pb-3 font-medium">Enabled</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rules.map((rule) => (
              <tr key={rule.id}>
                <td className="py-3 pr-4 font-medium text-slate-200">{rule.label}</td>
                <td className="max-w-sm py-3 pr-4 text-slate-400">{rule.description}</td>
                <td className="py-3 pr-4">
                  <Badge variant={SEVERITY_VARIANT[rule.severity] ?? "neutral"}>{rule.severity}</Badge>
                </td>
                <td className="py-3 pr-4 text-slate-400">v{rule.version}</td>
                <td className="py-3">
                  <button
                    onClick={() => onToggle(rule)}
                    role="switch"
                    aria-checked={rule.enabled}
                    className={`relative h-6 w-11 rounded-full transition-colors ${
                      rule.enabled ? "bg-brand-cyan" : "bg-white/10"
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                        rule.enabled ? "translate-x-[22px]" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AdminRulesPage() {
  const { showToast } = useToast();
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    adminService
      .listRules()
      .then(setRules)
      .catch((err) => setError(extractErrorMessage(err, "Could not load detection rules.")))
      .finally(() => setIsLoading(false));
  };

  useEffect(load, []);

  const handleToggle = async (rule: DetectionRule) => {
    const previous = rules;
    setRules((current) => current.map((r) => (r.id === rule.id ? { ...r, enabled: !r.enabled } : r)));
    try {
      const updated = await adminService.toggleRule(rule.id, !rule.enabled);
      setRules((current) => current.map((r) => (r.id === updated.id ? updated : r)));
      showToast(`${rule.label} ${updated.enabled ? "enabled" : "disabled"}.`, "success");
    } catch (err) {
      setRules(previous);
      showToast(extractErrorMessage(err, "Could not update this rule."), "error");
    }
  };

  const byCategory = (category: RuleCategory) => rules.filter((r) => r.category === category);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-50">
          <ListChecks size={22} />
          Rule Management
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Enable or disable individual detection rules. This never changes rule logic — only whether it runs.
        </p>
      </div>

      {error && <div className="glass-card border-danger/20 p-4 text-sm text-danger">{error}</div>}

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.03]" />
          ))}
        </div>
      ) : (
        <>
          <RuleTable title="URL Scanner Rules" rules={byCategory("url")} onToggle={handleToggle} />
          <RuleTable title="Email Scanner Rules" rules={byCategory("email")} onToggle={handleToggle} />
        </>
      )}
    </div>
  );
}

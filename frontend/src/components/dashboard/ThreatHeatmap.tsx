import type { HeatmapRow } from "@/types/dashboardIntel";

const LEVELS: { key: keyof Omit<HeatmapRow, "weekday">; label: string; classes: string }[] = [
  { key: "Safe", label: "Safe", classes: "bg-safe" },
  { key: "Low Risk", label: "Low Risk", classes: "bg-brand-cyan" },
  { key: "Suspicious", label: "Suspicious", classes: "bg-warning" },
  { key: "Dangerous", label: "Dangerous", classes: "bg-danger" },
];

export function ThreatHeatmap({ data }: { data: HeatmapRow[] }) {
  const max = Math.max(...data.flatMap((row) => LEVELS.map((l) => row[l.key])), 1);

  return (
    <div className="flex flex-col gap-2">
      {data.map((row) => (
        <div key={row.weekday} className="flex items-center gap-3">
          <span className="w-20 shrink-0 text-xs text-slate-400">{row.weekday.slice(0, 3)}</span>
          <div className="flex flex-1 gap-1">
            {LEVELS.map((level) => {
              const value = row[level.key];
              const opacity = value === 0 ? 0.06 : 0.25 + (value / max) * 0.75;
              return (
                <div
                  key={level.key}
                  title={`${level.label}: ${value}`}
                  className={`h-6 flex-1 rounded ${level.classes}`}
                  style={{ opacity }}
                />
              );
            })}
          </div>
        </div>
      ))}
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
        {LEVELS.map((level) => (
          <div key={level.key} className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span className={`h-2 w-2 rounded-full ${level.classes}`} />
            {level.label}
          </div>
        ))}
      </div>
    </div>
  );
}

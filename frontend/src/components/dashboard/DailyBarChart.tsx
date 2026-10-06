import type { DailyCount } from "@/types/dashboardIntel";

interface DailyBarChartProps {
  data: DailyCount[];
  barClassName?: string;
}

export function DailyBarChart({ data, barClassName = "bg-brand-cyan" }: DailyBarChartProps) {
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="flex h-32 items-end gap-1">
      {data.map((point) => {
        const heightPct = Math.max((point.count / max) * 100, point.count > 0 ? 6 : 2);
        return (
          <div
            key={point.date}
            className="group relative flex-1"
            title={`${new Date(point.date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}: ${point.count}`}
          >
            <div
              className={`w-full rounded-t-sm ${point.count > 0 ? barClassName : "bg-white/5"} transition-all duration-300 group-hover:brightness-125`}
              style={{ height: `${heightPct}%`, minHeight: "2px", position: "absolute", bottom: 0, left: 0, right: 0 }}
            />
          </div>
        );
      })}
    </div>
  );
}

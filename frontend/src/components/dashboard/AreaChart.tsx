interface AreaChartPoint {
  date: string;
  count: number;
}

interface AreaChartProps {
  data: AreaChartPoint[];
  height?: number;
  colorClassName?: string;
  colorHex?: string;
}

export function AreaChart({ data, height = 160, colorClassName = "text-brand-cyan", colorHex = "#22d3ee" }: AreaChartProps) {
  if (data.length === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-sm text-slate-500">No data yet.</div>;
  }

  const width = 600;
  const max = Math.max(...data.map((d) => d.count), 1);
  const step = data.length > 1 ? width / (data.length - 1) : 0;
  const gradientId = `area-gradient-${colorHex.replace("#", "")}`;

  const points = data.map((d, i) => {
    const x = i * step;
    const y = height - (d.count / max) * (height - 8) - 4;
    return { x, y };
  });

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${height} L0,${height} Z`;

  return (
    <div className={colorClassName}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={colorHex} stopOpacity="0.35" />
            <stop offset="100%" stopColor={colorHex} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />
        <path d={linePath} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        {points.map((p, i) => (
          <g key={data[i].date}>
            <circle cx={p.x} cy={p.y} r={2.5} fill={colorHex} />
            <title>
              {new Date(data[i].date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}: {data[i].count}
            </title>
          </g>
        ))}
      </svg>
      <div className="mt-1 flex justify-between text-[10px] text-slate-600">
        <span>{new Date(data[0].date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
        <span>{new Date(data[data.length - 1].date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
      </div>
    </div>
  );
}

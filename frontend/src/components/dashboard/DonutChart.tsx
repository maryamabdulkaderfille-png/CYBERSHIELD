interface DonutSegment {
  label: string;
  value: number;
  colorClassName: string;
  colorHex: string;
}

interface DonutChartProps {
  segments: DonutSegment[];
  size?: number;
  strokeWidth?: number;
  centerLabel?: string;
  centerValue?: string;
}

export function DonutChart({ segments, size = 160, strokeWidth = 18, centerLabel, centerValue }: DonutChartProps) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  let offset = 0;

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="currentColor" className="text-white/5" strokeWidth={strokeWidth} />
          {total > 0 &&
            segments.map((segment) => {
              if (segment.value <= 0) return null;
              const fraction = segment.value / total;
              const dash = fraction * circumference;
              const dashArray = `${dash} ${circumference - dash}`;
              const dashOffset = -offset;
              offset += dash;
              return (
                <circle
                  key={segment.label}
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="none"
                  stroke={segment.colorHex}
                  strokeWidth={strokeWidth}
                  strokeDasharray={dashArray}
                  strokeDashoffset={dashOffset}
                  strokeLinecap="butt"
                  className="transition-all duration-500"
                />
              );
            })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-slate-50">{centerValue ?? total}</span>
          {centerLabel && <span className="text-xs text-slate-500">{centerLabel}</span>}
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-2">
        {segments.map((segment) => {
          const pct = total > 0 ? Math.round((segment.value / total) * 100) : 0;
          return (
            <div key={segment.label} className="flex min-w-0 items-center gap-2 text-xs text-slate-400">
              <span className={`h-2 w-2 shrink-0 rounded-full ${segment.colorClassName}`} />
              <span className="min-w-0 flex-1 truncate">{segment.label}</span>
              <span className="shrink-0 font-medium text-slate-300">{segment.value}</span>
              <span className="w-9 shrink-0 text-right text-slate-500">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

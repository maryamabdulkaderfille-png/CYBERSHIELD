interface TrendSparklineProps {
  values: (number | null)[];
  colorClassName?: string;
  width?: number;
  height?: number;
}

export function TrendSparkline({
  values,
  colorClassName = "text-brand-cyan",
  width = 72,
  height = 24,
}: TrendSparklineProps) {
  const points = values.filter((v): v is number => v != null);
  if (points.length < 2) {
    return <div style={{ width, height }} />;
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = width / (values.length - 1);

  let path = "";
  values.forEach((v, i) => {
    if (v == null) return;
    const x = i * step;
    const y = height - ((v - min) / range) * height;
    path += `${path ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)} `;
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={colorClassName} aria-hidden="true">
      <path d={path.trim()} fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

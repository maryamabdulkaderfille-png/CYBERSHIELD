interface RankedBarListProps {
  items: { label: string; count: number }[];
  barClassName?: string;
  emptyText?: string;
}

export function RankedBarList({ items, barClassName = "bg-brand-cyan", emptyText = "No data yet." }: RankedBarListProps) {
  if (items.length === 0) {
    return <p className="py-6 text-center text-sm text-slate-500">{emptyText}</p>;
  }

  const max = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="w-32 shrink-0 truncate text-xs text-slate-400" title={item.label}>
            {item.label}
          </span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
            <div
              className={`h-full rounded-full ${barClassName}`}
              style={{ width: `${(item.count / max) * 100}%` }}
            />
          </div>
          <span className="w-6 shrink-0 text-right text-xs font-medium text-slate-300">{item.count}</span>
        </div>
      ))}
    </div>
  );
}

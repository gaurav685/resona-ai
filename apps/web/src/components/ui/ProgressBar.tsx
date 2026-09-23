export function ProgressBar({
  value,
  max = 1,
  color = "var(--series-1)",
  label,
  valueLabel,
}: {
  value: number;
  max?: number;
  color?: string;
  label?: string;
  valueLabel?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      {(label || valueLabel) && (
        <div className="flex items-baseline justify-between mb-1.5 text-sm">
          {label && <span style={{ color: "var(--text-secondary)" }}>{label}</span>}
          {valueLabel && <span className="font-medium tabular-nums">{valueLabel}</span>}
        </div>
      )}
      <div
        className="h-2 w-full overflow-hidden rounded-full"
        style={{ background: "var(--gridline)" }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className="h-full rounded-full transition-[width] duration-500 ease-out"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

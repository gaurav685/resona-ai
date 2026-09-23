export function Slider({
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.1,
  leftLabel,
  rightLabel,
  ariaLabel,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  leftLabel: string;
  rightLabel: string;
  ariaLabel: string;
}) {
  return (
    <div className="w-full">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={ariaLabel}
        className="w-full accent-[var(--accent)]"
        style={{ accentColor: "var(--accent)" }}
      />
      <div className="flex justify-between text-xs mt-1" style={{ color: "var(--text-muted)" }}>
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
}

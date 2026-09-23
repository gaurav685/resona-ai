import { LucideIcon } from "lucide-react";

export function StatTile({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon?: LucideIcon;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1" style={{ color: "var(--text-muted)" }}>
        {Icon && <Icon className="h-3.5 w-3.5" />}
        <span className="text-xs uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {hint && (
        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {hint}
        </div>
      )}
    </div>
  );
}

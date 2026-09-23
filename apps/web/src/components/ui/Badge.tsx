import { cn } from "@/lib/utils";

type BadgeTone = "neutral" | "accent" | "good" | "warning" | "critical";

const TONE_STYLE: Record<BadgeTone, React.CSSProperties> = {
  neutral: { color: "var(--text-secondary)", borderColor: "var(--border)" },
  accent: { color: "var(--accent)", borderColor: "var(--accent)" },
  good: { color: "var(--good)", borderColor: "var(--good)" },
  warning: { color: "var(--warning)", borderColor: "var(--warning)" },
  critical: { color: "var(--critical)", borderColor: "var(--critical)" },
};

export function Badge({
  className,
  children,
  tone = "neutral",
}: {
  className?: string;
  children: React.ReactNode;
  tone?: BadgeTone;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        className
      )}
      style={TONE_STYLE[tone]}
    >
      {children}
    </span>
  );
}

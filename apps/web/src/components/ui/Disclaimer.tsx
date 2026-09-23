import { Info } from "lucide-react";

export function Disclaimer({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex items-start gap-2 rounded-xl border px-4 py-3 text-sm"
      style={{ borderColor: "var(--border)", color: "var(--text-secondary)", background: "var(--surface)" }}
      role="note"
    >
      <Info className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "var(--text-muted)" }} />
      <p>{children}</p>
    </div>
  );
}

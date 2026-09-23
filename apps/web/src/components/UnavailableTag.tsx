import { Ban } from "lucide-react";

export function UnavailableTag({ label, reason }: { label: string; reason: string }) {
  return (
    <div className="flex items-start gap-1.5 text-xs" style={{ color: "var(--text-muted)" }} title={reason}>
      <Ban className="h-3 w-3 mt-0.5 shrink-0" />
      <span>
        <span className="font-medium">{label}:</span> not available — {reason}
      </span>
    </div>
  );
}

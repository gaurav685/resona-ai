import { LucideIcon, Inbox } from "lucide-react";

export function EmptyState({
  icon: Icon = Inbox,
  title = "Not enough listening history yet.",
  description,
}: {
  icon?: LucideIcon;
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <Icon className="h-8 w-8" style={{ color: "var(--text-muted)" }} />
      <p className="font-medium" style={{ color: "var(--text-secondary)" }}>
        {title}
      </p>
      {description && (
        <p className="max-w-sm text-sm" style={{ color: "var(--text-muted)" }}>
          {description}
        </p>
      )}
    </div>
  );
}

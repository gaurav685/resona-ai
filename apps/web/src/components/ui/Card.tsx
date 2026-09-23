import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border p-6 shadow-sm transition-colors",
        className
      )}
      style={{
        borderColor: "var(--border)",
        background: "var(--surface)",
      }}
    >
      {children}
    </div>
  );
}

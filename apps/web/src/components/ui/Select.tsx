import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function Select({
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative inline-block">
      <select
        className={cn(
          "appearance-none rounded-full border py-1.5 pl-3.5 pr-8 text-sm font-medium",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
          className
        )}
        style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
        style={{ color: "var(--text-muted)" }}
      />
    </div>
  );
}

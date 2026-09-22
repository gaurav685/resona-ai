import { cn } from "@/lib/utils";

export function Badge({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-black/10 dark:border-white/15 px-2.5 py-0.5 text-xs font-medium text-black/70 dark:text-white/70",
        className
      )}
    >
      {children}
    </span>
  );
}

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
        "rounded-2xl border border-black/10 dark:border-white/10 bg-white/60 dark:bg-white/[0.03] backdrop-blur-sm p-6 shadow-sm",
        className
      )}
    >
      {children}
    </div>
  );
}

import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";

const VARIANT_CLASS: Record<Variant, string> = {
  primary: "text-white",
  secondary: "border",
  ghost: "",
};

export function Button({
  className,
  variant = "secondary",
  active = false,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; active?: boolean }) {
  const style: React.CSSProperties =
    variant === "primary"
      ? { background: "var(--accent)" }
      : variant === "secondary"
        ? {
            borderColor: active ? "var(--accent)" : "var(--border)",
            color: active ? "var(--accent)" : "var(--foreground)",
            background: active ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
          }
        : { color: "var(--text-secondary)" };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        VARIANT_CLASS[variant],
        className
      )}
      style={{ ...style, outlineColor: "var(--accent)" }}
      {...props}
    >
      {children}
    </button>
  );
}

import { Music2 } from "lucide-react";

const UPCOMING_SECTIONS = ["Dashboard", "Personas", "Recommendations"];

export function NavBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-black/10 dark:border-white/10 bg-white/70 dark:bg-black/40 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 font-semibold tracking-tight">
          <Music2 className="h-5 w-5" />
          <span>Resona AI</span>
        </div>
        <nav className="flex gap-4 text-sm text-black/40 dark:text-white/40">
          {UPCOMING_SECTIONS.map((label) => (
            <span key={label} className="cursor-not-allowed" title="Coming in a later phase">
              {label}
            </span>
          ))}
        </nav>
      </div>
    </header>
  );
}

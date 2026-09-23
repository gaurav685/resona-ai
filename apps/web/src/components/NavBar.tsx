"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Music2 } from "lucide-react";
import { UserPicker } from "./UserPicker";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/listening-dna", label: "Listening DNA" },
  { href: "/personality", label: "Personality" },
  { href: "/persona", label: "Persona" },
  { href: "/current-state", label: "Current State" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/taste-evolution", label: "Evolution" },
  { href: "/about", label: "About" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header
      className="sticky top-0 z-10 border-b backdrop-blur-md"
      style={{ borderColor: "var(--border)", background: "color-mix(in srgb, var(--background) 85%, transparent)" }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight shrink-0">
          <Music2 className="h-5 w-5" style={{ color: "var(--accent)" }} />
          <span>Resona AI</span>
        </Link>
        <nav className="flex gap-1 overflow-x-auto text-sm" aria-label="Main">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "whitespace-nowrap rounded-full px-3 py-1.5 transition-colors",
                  active ? "font-medium" : ""
                )}
                style={{
                  color: active ? "var(--accent)" : "var(--text-secondary)",
                  background: active ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
                }}
                aria-current={active ? "page" : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="shrink-0">
          <UserPicker />
        </div>
      </div>
    </header>
  );
}

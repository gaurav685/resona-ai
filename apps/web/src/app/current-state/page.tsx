"use client";

import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { UnavailableTag } from "@/components/UnavailableTag";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/format";
import type { WindowStats } from "@/lib/types";

const WINDOWS: { key: "last_5" | "last_10" | "current_session" | "last_30_min"; label: string }[] = [
  { key: "last_5", label: "Last 5 tracks" },
  { key: "last_10", label: "Last 10 tracks" },
  { key: "current_session", label: "Current session" },
  { key: "last_30_min", label: "Last 30 minutes" },
];

function Shift({ label, value, unit = "" }: { label: string; value: number | null; unit?: string }) {
  if (value === null) return null;
  const positive = value > 0;
  const color = value === 0 ? "var(--text-muted)" : positive ? "var(--good)" : "var(--critical)";
  return (
    <div className="flex items-center justify-between text-sm py-1.5">
      <span style={{ color: "var(--text-secondary)" }}>{label}</span>
      <span className="font-medium tabular-nums" style={{ color }}>
        {positive ? "+" : ""}
        {value.toFixed(unit === "s" ? 0 : 2)}
        {unit}
      </span>
    </div>
  );
}

export default function CurrentStatePage() {
  const { userId } = useUser();
  const context = useApi(userId ? () => api.getCurrentContext(userId) : null, [userId]);

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <PageHeader
        title="Current State"
        description={userId ? `Recent listening activity for ${userId}, compared against their own historical baseline.` : "Select a listener."}
      />

      {(!userId || context.isLoading) && <SkeletonCard />}
      {context.isError && <ErrorState message={context.error ?? "Failed to load."} onRetry={context.refetch} />}

      {context.data && (
        <div className="space-y-4">
          <Card>
            <Badge tone="accent" className="mb-2">
              {context.data.context_label}
            </Badge>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {context.data.context_explanation}
            </p>
            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
              {context.data.disclaimer}
            </p>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {WINDOWS.map(({ key, label }) => {
              const w: WindowStats = context.data!.windows[key];
              return (
                <Card key={key}>
                  <h3 className="text-xs uppercase tracking-wide mb-2" style={{ color: "var(--text-muted)" }}>
                    {label}
                  </h3>
                  {w.n_events === 0 ? (
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                      No events
                    </p>
                  ) : (
                    <div className="space-y-1 text-sm">
                      <div>{w.n_events} events</div>
                      <div style={{ color: "var(--text-secondary)" }}>Diversity: {formatPercent(w.artist_diversity)}</div>
                      <div style={{ color: "var(--text-secondary)" }}>Repeat: {formatPercent(w.repeat_rate)}</div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="font-medium mb-2">Shift vs. Personal Baseline</h2>
              <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
                Current session compared to this listener&apos;s history before it.
              </p>
              <div className="divide-y" style={{ borderColor: "var(--border)" }}>
                <Shift label="Artist diversity shift" value={context.data.shifts.diversity_shift} />
                <Shift label="Repeat-rate shift" value={context.data.shifts.repeat_shift} />
                <Shift label="Night-listening shift" value={context.data.shifts.night_shift} />
                <Shift label="Pace shift" value={context.data.shifts.pace_shift_sec} unit="s" />
              </div>
            </Card>

            <Card>
              <h2 className="font-medium mb-3">Not Available For This Dataset</h2>
              <div className="space-y-2">
                <UnavailableTag label="Energy" reason={context.data.shifts.energy_shift_unavailable_reason} />
                <UnavailableTag label="Valence" reason={context.data.shifts.valence_shift_unavailable_reason} />
                <UnavailableTag label="Tempo" reason={context.data.shifts.tempo_shift_unavailable_reason} />
                <UnavailableTag label="Genre" reason={context.data.shifts.genre_shift_unavailable_reason} />
              </div>
              <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                Baseline events: {formatNumber(context.data.baseline.n_events ?? null, 0)}
              </p>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

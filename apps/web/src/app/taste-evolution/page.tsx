"use client";

import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { MetricLineChart } from "@/components/charts/MetricLineChart";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatPercent } from "@/lib/format";

export default function TasteEvolutionPage() {
  const { userId } = useUser();
  const evolution = useApi(userId ? () => api.getTasteEvolution(userId) : null, [userId]);

  const periods = evolution.data?.periods ?? [];

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <PageHeader
        title="Taste Evolution"
        description={userId ? `Real monthly listening-behavior trends for ${userId}, binned from actual event timestamps.` : "Select a listener."}
      />

      {(!userId || evolution.isLoading) && <SkeletonCard />}
      {evolution.isError && <ErrorState message={evolution.error ?? "Failed to load."} onRetry={evolution.refetch} />}

      {evolution.data && periods.length === 0 && <EmptyState title="Not enough listening history yet." />}

      {evolution.data && periods.length === 1 && (
        <EmptyState
          title="Only one time period in this listener's sample."
          description="A trend needs at least two months of data — this listener's capped event sample falls in a single month."
        />
      )}

      {evolution.data && periods.length > 1 && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h2 className="font-medium mb-1">Listening Frequency</h2>
            <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              Events per active day, by month
            </p>
            <MetricLineChart data={periods} dataKey="listening_frequency" color="var(--series-1)" valueFormatter={(v) => v.toFixed(1)} />
          </Card>
          <Card>
            <h2 className="font-medium mb-1">Artist Diversity</h2>
            <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              Unique artists / plays, by month
            </p>
            <MetricLineChart data={periods} dataKey="artist_diversity" color="var(--series-3)" valueFormatter={(v) => formatPercent(v)} />
          </Card>
          <Card>
            <h2 className="font-medium mb-1">Discovery Rate</h2>
            <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              Share of plays that were a new artist for this listener, by month
            </p>
            <MetricLineChart data={periods} dataKey="discovery_rate" color="var(--series-2)" valueFormatter={(v) => formatPercent(v)} />
          </Card>
          <Card>
            <h2 className="font-medium mb-1">Unique Artists</h2>
            <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              Distinct artists played, by month
            </p>
            <MetricLineChart data={periods} dataKey="unique_artists" color="var(--series-4)" valueFormatter={(v) => String(v)} />
          </Card>
        </div>
      )}
    </div>
  );
}

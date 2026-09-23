"use client";

import Link from "next/link";
import { ArrowRight, Activity, Compass, Users2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatTile } from "@/components/ui/StatTile";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/format";

export default function DashboardPage() {
  const { userId } = useUser();

  const dna = useApi(userId ? () => api.getListeningDNA(userId) : null, [userId]);
  const context = useApi(userId ? () => api.getCurrentContext(userId) : null, [userId]);
  const persona = useApi(userId ? () => api.getPersona(userId) : null, [userId]);
  const recs = useApi(userId ? () => api.getRecommendations(userId, { limit: 3 }) : null, [userId]);

  if (!userId) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        title={`Dashboard — ${userId}`}
        description="A snapshot of this listener's Listening DNA, current context, discovered persona, and top recommendations — every number below comes from a real API call."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Listening DNA summary */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-4 w-4" style={{ color: "var(--accent)" }} />
            <h2 className="font-medium">Listening DNA</h2>
            <Link href="/listening-dna" className="ml-auto text-xs flex items-center gap-0.5" style={{ color: "var(--accent)" }}>
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {dna.isLoading && <SkeletonRow />}
          {dna.isError && <ErrorState message={dna.error ?? "Failed to load."} onRetry={dna.refetch} />}
          {dna.data && (
            <div className="grid grid-cols-2 gap-4">
              <StatTile label="Events" value={String(dna.data.n_events)} />
              <StatTile label="Sessions" value={String(dna.data.n_sessions)} />
              <StatTile label="Artist diversity" value={formatPercent(dna.data.artist_diversity)} />
              <StatTile label="Discovery rate" value={formatPercent(dna.data.discovery_rate)} />
            </div>
          )}
        </Card>

        {/* Current context */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Compass className="h-4 w-4" style={{ color: "var(--accent)" }} />
            <h2 className="font-medium">Current Context</h2>
            <Link href="/current-state" className="ml-auto text-xs flex items-center gap-0.5" style={{ color: "var(--accent)" }}>
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {context.isLoading && <SkeletonRow />}
          {context.isError && <ErrorState message={context.error ?? "Failed to load."} onRetry={context.refetch} />}
          {context.data && (
            <div>
              <Badge tone="accent" className="mb-2">
                {context.data.context_label}
              </Badge>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {context.data.context_explanation}
              </p>
            </div>
          )}
        </Card>

        {/* Persona */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Users2 className="h-4 w-4" style={{ color: "var(--accent)" }} />
            <h2 className="font-medium">Listener Persona</h2>
            <Link href="/persona" className="ml-auto text-xs flex items-center gap-0.5" style={{ color: "var(--accent)" }}>
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {persona.isLoading && <SkeletonRow />}
          {persona.isError && (
            <EmptyState
              title="Not enough listening history yet."
              description={persona.error ?? undefined}
            />
          )}
          {persona.data && (
            <div>
              <p className="font-medium">{persona.data.persona_name}</p>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                Cluster of {persona.data.cluster_size} listeners · silhouette {formatNumber(persona.data.silhouette_score, 2)}
              </p>
            </div>
          )}
        </Card>

        {/* Personality note */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4" style={{ color: "var(--accent)" }} />
            <h2 className="font-medium">Personality</h2>
            <Link href="/personality" className="ml-auto text-xs flex items-center gap-0.5" style={{ color: "var(--accent)" }}>
              Try it <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No personality labels exist for Last.fm listeners like {userId} — the personality
            model is demonstrated separately on real research-participant data, never fabricated
            for a behavioral demo user.
          </p>
        </Card>
      </div>

      {/* Recommendation preview */}
      <Card className="mt-4">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="font-medium">Top Recommendations</h2>
          <Link href="/recommendations" className="ml-auto text-xs flex items-center gap-0.5" style={{ color: "var(--accent)" }}>
            See all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        {recs.isLoading && <SkeletonRow />}
        {recs.isError && <ErrorState message={recs.error ?? "Failed to load."} onRetry={recs.refetch} />}
        {recs.data && recs.data.recommendations.length === 0 && <EmptyState />}
        {recs.data && recs.data.recommendations.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-3">
            {recs.data.recommendations.map((r) => (
              <div key={r.recommendation_id} className="rounded-xl border p-3" style={{ borderColor: "var(--border)" }}>
                <p className="text-sm font-medium truncate">{r.track_title}</p>
                <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                  {r.artist_name}
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="space-y-2">
      <div className="h-4 w-2/3 rounded animate-pulse-soft" style={{ background: "var(--gridline)" }} />
      <div className="h-4 w-1/2 rounded animate-pulse-soft" style={{ background: "var(--gridline)" }} />
    </div>
  );
}

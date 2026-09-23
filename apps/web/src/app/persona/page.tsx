"use client";

import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatTile } from "@/components/ui/StatTile";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ZScoreChart } from "@/components/charts/ZScoreChart";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatFeatureName, formatNumber } from "@/lib/format";

export default function PersonaPage() {
  const { userId } = useUser();
  const persona = useApi(userId ? () => api.getPersona(userId) : null, [userId]);

  const zScoreEntries = persona.data
    ? Object.entries(persona.data.cluster_feature_z_scores).map(([feature, z]) => ({ feature, z }))
    : [];
  const topDrivers = [...zScoreEntries].sort((a, b) => Math.abs(b.z) - Math.abs(a.z)).slice(0, 2);

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <PageHeader
        title="Listener Persona"
        description={userId ? `Discovered behavioral cluster for ${userId}, from unsupervised KMeans over real Listening DNA features.` : "Select a listener."}
      />

      {(!userId || persona.isLoading) && <SkeletonCard />}

      {persona.isError && (
        <EmptyState
          title="Not enough listening history yet."
          description={
            persona.errorStatus === 404
              ? "This listener has too few events to be included in the clustering run (minimum 20)."
              : (persona.error ?? undefined)
          }
        />
      )}

      {persona.data && (
        <div className="space-y-4">
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <Badge tone="accent" className="mb-2">
                  {persona.data.algorithm} · {persona.data.model_version}
                </Badge>
                <h2 className="text-xl font-semibold">{persona.data.persona_name}</h2>
                <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
                  Cluster name is auto-derived from this cluster&apos;s two most distinguishing
                  features — never a hard-coded label.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <StatTile label="Cluster size" value={`${persona.data.cluster_size} listeners`} />
                <StatTile label="Silhouette score" value={formatNumber(persona.data.silhouette_score, 3)} hint="Cluster separation quality" />
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="font-medium mb-1">Why this cluster?</h2>
            <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
              {topDrivers.length === 2 && (
                <>
                  This cluster is most distinguished by{" "}
                  <strong>{topDrivers[0].z >= 0 ? "high" : "low"} {formatFeatureName(topDrivers[0].feature).toLowerCase()}</strong>{" "}
                  ({topDrivers[0].z >= 0 ? "+" : ""}{topDrivers[0].z.toFixed(2)}σ vs. the average listener) and{" "}
                  <strong>{topDrivers[1].z >= 0 ? "high" : "low"} {formatFeatureName(topDrivers[1].feature).toLowerCase()}</strong>{" "}
                  ({topDrivers[1].z >= 0 ? "+" : ""}{topDrivers[1].z.toFixed(2)}σ).
                </>
              )}
            </p>
            <ZScoreChart data={zScoreEntries} />
            <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
              σ = standard deviations from the average listener across all 983 clustered users,
              on each real Listening DNA feature.
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}

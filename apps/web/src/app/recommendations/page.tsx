"use client";

import { useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Slider } from "@/components/ui/Slider";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { RecommendationCard } from "@/components/RecommendationCard";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";

const CONTEXT_OPTIONS = ["auto", "Exploratory", "Focused", "Reflective", "Routine"];

export default function RecommendationsPage() {
  const { userId } = useUser();
  const [novelty, setNovelty] = useState(0.2);
  const [contextOverride, setContextOverride] = useState("auto");

  const recs = useApi(
    userId
      ? () =>
          api.getRecommendations(userId, {
            limit: 12,
            novelty,
            context: contextOverride === "auto" ? undefined : contextOverride,
          })
      : null,
    [userId, novelty, contextOverride]
  );

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        title="Recommendations"
        description={userId ? `Hybrid recommendations for ${userId} — content/co-listening similarity, artist preference, context alignment, and novelty, combined and diversity-reranked.` : "Select a listener."}
      />

      <Card className="mb-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <span className="text-sm font-medium mb-2 block">Novelty</span>
            <Slider
              value={novelty}
              onChange={setNovelty}
              leftLabel="Low"
              rightLabel="High"
              ariaLabel="Novelty preference"
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block" htmlFor="context-select">
              Listening context
            </label>
            <Select id="context-select" value={contextOverride} onChange={(e) => setContextOverride(e.target.value)}>
              {CONTEXT_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c === "auto" ? "Auto-detect" : c}
                </option>
              ))}
            </Select>
          </div>
        </div>
        {recs.data && (
          <p className="text-xs mt-4" style={{ color: "var(--text-muted)" }}>
            Detected context: <Badge tone="accent">{recs.data.context_label}</Badge>{" "}
            &middot; weights used: co-listening {(recs.data.weights_used.co_listening_similarity * 100).toFixed(0)}%,
            artist preference {(recs.data.weights_used.artist_preference * 100).toFixed(0)}%, context{" "}
            {(recs.data.weights_used.context_alignment * 100).toFixed(0)}%, novelty{" "}
            {(recs.data.weights_used.novelty * 100).toFixed(0)}%
          </p>
        )}
      </Card>

      {(!userId || recs.isLoading) && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {recs.isError && <ErrorState message={recs.error ?? "Failed to load."} onRetry={recs.refetch} />}

      {recs.data && recs.data.recommendations.length === 0 && (
        <EmptyState description="This listener has no eligible candidates right now — try adjusting novelty or context." />
      )}

      {recs.data && recs.data.recommendations.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recs.data.recommendations.map((item) => (
            <RecommendationCard key={item.recommendation_id} item={item} onFeedback={() => {}} />
          ))}
        </div>
      )}

      {recs.data && (
        <p className="text-xs mt-6 max-w-2xl" style={{ color: "var(--text-muted)" }}>
          {recs.data.note}
        </p>
      )}
    </div>
  );
}

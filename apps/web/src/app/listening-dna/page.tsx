"use client";

import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { UnavailableTag } from "@/components/UnavailableTag";
import { TopArtistsChart } from "@/components/charts/TopArtistsChart";
import { useUser } from "@/lib/user-context";
import { useApi } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import type { ListeningDNA } from "@/lib/types";

const UNAVAILABLE_FIELDS: { key: keyof ListeningDNA; label: string }[] = [
  { key: "genre_diversity", label: "Genre diversity" },
  { key: "completion_rate", label: "Completion rate" },
  { key: "skip_rate", label: "Skip rate" },
  { key: "energy", label: "Energy" },
  { key: "valence", label: "Valence" },
  { key: "danceability", label: "Danceability" },
  { key: "tempo", label: "Tempo" },
  { key: "acousticness", label: "Acousticness" },
  { key: "instrumentalness", label: "Instrumentalness" },
  { key: "speechiness", label: "Speechiness" },
];

export default function ListeningDNAPage() {
  const { userId } = useUser();
  const dna = useApi(userId ? () => api.getListeningDNA(userId) : null, [userId]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        title="Listening DNA"
        description={userId ? `Behavioral fingerprint for ${userId}, computed from real Last.fm listening events.` : "Select a listener."}
      />

      {(!userId || dna.isLoading) && <SkeletonCard />}
      {dna.isError && <ErrorState message={dna.error ?? "Failed to load."} onRetry={dna.refetch} />}

      {dna.data && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <Card>
              <StatTile label="Events" value={String(dna.data.n_events)} />
            </Card>
            <Card>
              <StatTile label="Sessions" value={String(dna.data.n_sessions)} />
            </Card>
            <Card>
              <StatTile label="Artist diversity" value={formatPercent(dna.data.artist_diversity)} />
            </Card>
            <Card>
              <StatTile label="Discovery rate" value={formatPercent(dna.data.discovery_rate)} />
            </Card>
            <Card>
              <StatTile label="Replay rate" value={formatPercent(dna.data.replay_rate)} />
            </Card>
            <Card>
              <StatTile label="Repeat rate" value={formatPercent(dna.data.repeat_rate)} />
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="font-medium mb-4">Top Artists</h2>
              {dna.data.top_artists.length === 0 ? (
                <EmptyState />
              ) : (
                <TopArtistsChart data={dna.data.top_artists} />
              )}
            </Card>

            <div className="space-y-4">
              <Card>
                <h2 className="font-medium mb-4">Temporal Patterns</h2>
                <div className="space-y-4">
                  <ProgressBar
                    label="Night listening (22:00–06:00 UTC)"
                    value={dna.data.night_listening_ratio_utc ?? 0}
                    valueLabel={formatPercent(dna.data.night_listening_ratio_utc)}
                    color="var(--series-7)"
                  />
                  <ProgressBar
                    label="Weekend listening"
                    value={dna.data.weekend_listening_ratio_utc ?? 0}
                    valueLabel={formatPercent(dna.data.weekend_listening_ratio_utc)}
                    color="var(--series-3)"
                  />
                  <ProgressBar
                    label="Artist concentration (HHI)"
                    value={dna.data.artist_concentration ?? 0}
                    valueLabel={formatPercent(dna.data.artist_concentration, 1)}
                    color="var(--series-4)"
                  />
                </div>
                <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                  Night/weekend ratios use event UTC timestamps, not the listener&apos;s local
                  time zone (not available in the source data).
                </p>
              </Card>

              <Card>
                <h2 className="font-medium mb-3">Not Available For This Dataset</h2>
                <div className="space-y-2">
                  {UNAVAILABLE_FIELDS.map(({ key, label }) => {
                    const reason = dna.data![`${key}_unavailable_reason` as keyof ListeningDNA] as string | null;
                    return reason ? <UnavailableTag key={key} label={label} reason={reason} /> : null;
                  })}
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

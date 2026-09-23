"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { TraitBar } from "@/components/TraitBar";
import { api, ApiError } from "@/lib/api";
import type { PersonalityPredictResponse, SampleParticipant } from "@/lib/types";

export default function PersonalityPage() {
  const [participants, setParticipants] = useState<SampleParticipant[] | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  const [prediction, setPrediction] = useState<PersonalityPredictResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSampleParticipants()
      .then((res) => {
        setParticipants(res.participants);
        if (res.participants.length > 0) setSelectedId(res.participants[0].participant_id);
      })
      .catch((e: unknown) => setLoadError(e instanceof ApiError ? e.message : "Failed to load."));
  }, []);

  useEffect(() => {
    const participant = participants?.find((p) => p.participant_id === selectedId);
    if (!participant) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: mark predicting before the async call starts
    setPredicting(true);
    setPredictError(null);
    api
      .predictPersonality(participant.features)
      .then(setPrediction)
      .catch((e: unknown) => setPredictError(e instanceof ApiError ? e.message : "Prediction failed."))
      .finally(() => setPredicting(false));
  }, [selectedId, participants]);

  const participant = participants?.find((p) => p.participant_id === selectedId);

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <PageHeader
        title="Personality"
        description="Model-estimated Big Five associations from the beyond_big_five research dataset — real participants, real audio-preference features."
      />

      <Disclaimer>
        These are model-estimated associations from music-listening preference data, not
        psychological diagnoses. No personality data exists for Last.fm listeners in this MVP —
        this page demonstrates the model on real research participants instead of fabricating a
        score for a behavioral demo user.
      </Disclaimer>

      <div className="mt-6">
        {loadError && <ErrorState message={loadError} />}
        {!participants && !loadError && <SkeletonCard />}

        {participants && (
          <Card>
            <div className="flex items-center justify-between gap-4 mb-4">
              <label className="text-sm font-medium" htmlFor="participant-select">
                Research participant
              </label>
              <Select id="participant-select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                {participants.map((p) => (
                  <option key={p.participant_id} value={p.participant_id}>
                    Participant #{p.participant_id}
                  </option>
                ))}
              </Select>
            </div>

            {predicting && (
              <div className="py-6 text-sm" style={{ color: "var(--text-muted)" }}>
                Running Random Forest inference…
              </div>
            )}
            {predictError && <ErrorState message={predictError} />}

            {prediction && participant && !predicting && (
              <div>
                <div className="divide-y" style={{ borderColor: "var(--border)" }}>
                  {prediction.predictions.map((p) => (
                    <TraitBar key={p.trait} prediction={p} actual={participant.actual_traits[p.trait]} />
                  ))}
                </div>
                <p className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
                  Model: {prediction.predictions[0]?.model_version}. &quot;Actual&quot; is this
                  participant&apos;s self-reported BFI-2 score from the source dataset, shown for
                  transparency — the model was not always close to it (see MODEL_CARD.md for
                  honest evaluation metrics, including negative R² on this small dataset).
                </p>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

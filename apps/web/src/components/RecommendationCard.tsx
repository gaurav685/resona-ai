"use client";

import { useState } from "react";
import { Heart, ThumbsDown, Bookmark, EyeOff, Sparkles, Loader2, Check } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { formatReasonCode } from "@/lib/format";
import type { FeedbackType, RecommendedItem } from "@/lib/types";

export function RecommendationCard({
  item,
  onFeedback,
}: {
  item: RecommendedItem;
  onFeedback: (type: FeedbackType) => void;
}) {
  const [sending, setSending] = useState<FeedbackType | null>(null);
  const [sent, setSent] = useState<FeedbackType | null>(null);

  async function handleFeedback(type: FeedbackType) {
    setSending(type);
    try {
      await api.submitFeedback(item.recommendation_id, type);
      setSent(type);
      onFeedback(type);
    } finally {
      setSending(null);
    }
  }

  const isExcluded = sent === "hide" || sent === "dislike";

  return (
    <Card className={`animate-fade-in transition-opacity ${isExcluded ? "opacity-40" : ""}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="font-medium truncate">{item.track_title}</h3>
          <p className="text-sm truncate" style={{ color: "var(--text-secondary)" }}>
            {item.artist_name}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0 text-sm font-medium tabular-nums" style={{ color: "var(--accent)" }}>
          <Sparkles className="h-3.5 w-3.5" />
          {(item.score * 100).toFixed(0)}
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {item.reason_codes.map((code) => (
          <Badge key={code} tone="accent">
            {formatReasonCode(code)}
          </Badge>
        ))}
      </div>

      <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
        {item.explanation}
      </p>

      <div className="mt-4 flex items-center gap-1.5" role="group" aria-label="Feedback">
        <FeedbackButton icon={Heart} label="Like" active={sent === "like"} busy={sending === "like"} onClick={() => handleFeedback("like")} />
        <FeedbackButton icon={ThumbsDown} label="Dislike" active={sent === "dislike"} busy={sending === "dislike"} onClick={() => handleFeedback("dislike")} />
        <FeedbackButton icon={Bookmark} label="Save" active={sent === "save"} busy={sending === "save"} onClick={() => handleFeedback("save")} />
        <FeedbackButton icon={EyeOff} label="Hide" active={sent === "hide"} busy={sending === "hide"} onClick={() => handleFeedback("hide")} />
      </div>
      {isExcluded && (
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Recorded — this track will be excluded from future recommendations for this listener.
        </p>
      )}
    </Card>
  );
}

function FeedbackButton({
  icon: Icon,
  label,
  active,
  busy,
  onClick,
}: {
  icon: typeof Heart;
  label: string;
  active: boolean;
  busy: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={busy}
      aria-pressed={active}
      aria-label={label}
      title={label}
      className="inline-flex items-center justify-center h-8 w-8 rounded-full border transition-colors focus-visible:outline focus-visible:outline-2"
      style={{
        borderColor: active ? "var(--accent)" : "var(--border)",
        color: active ? "var(--accent)" : "var(--text-secondary)",
        background: active ? "color-mix(in srgb, var(--accent) 12%, transparent)" : "transparent",
        outlineColor: "var(--accent)",
      }}
    >
      {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : active ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
    </button>
  );
}

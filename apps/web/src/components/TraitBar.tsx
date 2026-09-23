import { ProgressBar } from "@/components/ui/ProgressBar";
import { formatFeatureName } from "@/lib/format";
import type { TraitPrediction } from "@/lib/types";

// Big Five traits are measured 1-5 on this dataset's Likert scale.
const SCALE_MAX = 5;

export function TraitBar({ prediction, actual }: { prediction: TraitPrediction; actual?: number }) {
  return (
    <div className="py-3">
      <ProgressBar
        value={prediction.score}
        max={SCALE_MAX}
        label={prediction.trait}
        valueLabel={prediction.score.toFixed(2)}
      />
      <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs" style={{ color: "var(--text-muted)" }}>
        {prediction.confidence !== null ? (
          <span>± {prediction.confidence.toFixed(2)} (tree-ensemble std. dev.)</span>
        ) : (
          <span>{prediction.confidence_note}</span>
        )}
        {actual !== undefined && <span>Actual (self-reported): {actual.toFixed(2)}</span>}
      </div>
      {prediction.important_features.length > 0 && (
        <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
          Top contributing features:{" "}
          {prediction.important_features
            .slice(0, 3)
            .map((f) => formatFeatureName(f.feature))
            .join(", ")}
        </div>
      )}
    </div>
  );
}

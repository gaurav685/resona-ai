import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/Badge";

const DATASETS = [
  {
    name: "Last.fm 1K",
    use: "Behavioral data — 992 real users, 288,965 listening events, sessionized. Powers Listening DNA, Context Intelligence, Persona Discovery, and the hybrid Recommendation Engine.",
    limits: "No audio features, genre, or skip/duration data exists for these tracks.",
  },
  {
    name: "Beyond the Big Five (Kleć et al., 2023)",
    use: "279 real research participants with self-reported BFI-2 Big Five scores and real per-song audio/emotion features. The only dataset with legitimate personality-model inputs.",
    limits: "Not linked to Last.fm users — no personality data exists for the behavioral demo listeners.",
  },
  {
    name: "Million Song Dataset (sample)",
    use: "Track/artist identity metadata (1M tracks, 13,850 artists with geolocation).",
    limits: "No audio features in the metadata-only subset used here.",
  },
  {
    name: "DEAM",
    use: "1,802 real valence/arousal emotion annotations plus per-track genre metadata.",
    limits: "Own disjoint track catalog — not linked to Last.fm or MSD track identities.",
  },
];

const PIPELINE = [
  { title: "Listening DNA", body: "10 behavioral features computed directly from real event timestamps and artist identity (frequency, session stats, diversity, discovery, replay, temporal ratios). Audio-content features (energy, valence, tempo...) are explicitly reported unavailable — never approximated." },
  { title: "Personality model", body: "Linear Regression, Random Forest, and XGBoost trained on the 279-participant research dataset (32 real input features: 29 audio/emotion + 3 attitude ratings), plus a GPU-trained PyTorch feed-forward network, compared on identical test-set MAE. Random Forest won on the actual numbers — the neural net did not." },
  { title: "Persona discovery", body: "KMeans over real Listening DNA features, k selected by silhouette score (k=3 selected, silhouette 0.239). DBSCAN was tried and found no useful structure. Cluster names are auto-derived from each cluster's top z-score features — never hard-coded." },
  { title: "Context intelligence", body: "Rule-based classification (Exploratory / Focused / Reflective / Routine) from real behavioral shift signals — a session's artist/diversity/repeat/night/pace stats vs. that listener's own prior baseline. No trained classifier, no ground-truth labels to score against." },
  { title: "Recommendation engine", body: "Candidate generation from the top-1,500 Last.fm items by unique listeners -> filtering -> weighted scoring (co-listening similarity, artist preference, context alignment, novelty) -> MMR diversity rerank capped at 2 tracks/artist. Beat a most-popular baseline on every offline metric in Phase 4 evaluation." },
  { title: "Explainability", body: "Every recommendation persists its full score breakdown as structured evidence in SQLite. The explanation text is deterministically generated from that stored evidence at read time — never an LLM, never invented after the fact." },
  { title: "Feedback loop", body: "Like / dislike / skip / save / replay / hide feed a simple, bounded per-artist preference multiplier and a hard exclusion list for dislike/hide — no reinforcement learning, no bandits." },
];

const TRAINING_RUN = {
  model: "PyTorch feed-forward net (32->64->32->5), MSE loss, Adam",
  device: "CUDA",
  gpu: "NVIDIA GeForce RTX 3050 Ti Laptop GPU",
  pytorch: "2.14.0+cu126",
  cuda: "12.6",
  epochsRequested: 100,
  epochsCompleted: 88,
  bestEpoch: 78,
  bestValLoss: 0.5653,
  outcome: "Not selected — Random Forest had lower test-set MAE (0.615 vs 0.643). Kept as an experimental artifact.",
};

const LIMITATIONS = [
  "279 participants is a small sample for 5-target regression on 32 features — R² is negative for nearly every trait/model, meaning these models currently explain less test variance than the training mean.",
  "Last.fm behavioral data and the personality/audio-feature datasets have disjoint identity spaces — no single listener has both real behavioral and real personality data.",
  "The recommendation candidate pool is capped at the 1,500 most-listened-to items for tractability — absolute precision/recall are low as a real consequence, not a display bug.",
  "night/weekend listening ratios use UTC timestamps, not the listener's true local time zone (not present in the source data).",
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <PageHeader
        title="Methodology"
        description="What Resona is built on, how each layer actually works, and where it's honestly limited."
      />

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4">Datasets</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {DATASETS.map((d) => (
            <Card key={d.name}>
              <h3 className="font-medium text-sm mb-1">{d.name}</h3>
              <p className="text-sm mb-2" style={{ color: "var(--text-secondary)" }}>
                {d.use}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Limit: {d.limits}
              </p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4">Pipeline</h2>
        <div className="space-y-4">
          {PIPELINE.map((p) => (
            <div key={p.title}>
              <h3 className="font-medium text-sm">{p.title}</h3>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4">A recorded GPU training run</h2>
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Badge tone="accent">Actual recorded values — not live-fetched</Badge>
          </div>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <dt style={{ color: "var(--text-muted)" }}>Model</dt>
            <dd>{TRAINING_RUN.model}</dd>
            <dt style={{ color: "var(--text-muted)" }}>Device</dt>
            <dd>{TRAINING_RUN.device}</dd>
            <dt style={{ color: "var(--text-muted)" }}>GPU</dt>
            <dd>{TRAINING_RUN.gpu}</dd>
            <dt style={{ color: "var(--text-muted)" }}>PyTorch / CUDA</dt>
            <dd>{TRAINING_RUN.pytorch} / {TRAINING_RUN.cuda}</dd>
            <dt style={{ color: "var(--text-muted)" }}>Epochs requested / completed</dt>
            <dd>{TRAINING_RUN.epochsRequested} / {TRAINING_RUN.epochsCompleted} (early stopped)</dd>
            <dt style={{ color: "var(--text-muted)" }}>Best epoch</dt>
            <dd>{TRAINING_RUN.bestEpoch} (val loss {TRAINING_RUN.bestValLoss})</dd>
          </dl>
          <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
            Outcome: {TRAINING_RUN.outcome}
          </p>
        </Card>
      </section>

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-4">Limitations</h2>
        <ul className="space-y-2 text-sm list-disc pl-5" style={{ color: "var(--text-secondary)" }}>
          {LIMITATIONS.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Privacy &amp; Data Handling</h2>
        <Card>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            This is a college research MVP using only public research datasets (Last.fm 1K,
            beyond_big_five, MSD, DEAM) — no real individuals&apos; private data is collected by
            this app. Recommendation evidence and feedback you submit while using this demo are
            stored locally in this instance&apos;s SQLite database for the explainability and
            feedback-loop features to function, and are not sent anywhere else.
          </p>
        </Card>
      </section>
    </div>
  );
}

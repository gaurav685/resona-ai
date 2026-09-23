import Link from "next/link";
import { ArrowRight, Brain, Radio, Sparkles, Users2, Activity, Database, Cpu, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const FLOW = [
  { icon: Activity, label: "Listening Behavior", detail: "Real events from the Last.fm 1K research dataset" },
  { icon: Cpu, label: "AI Intelligence", detail: "Feature engineering, classical + neural models, clustering" },
  { icon: Brain, label: "Personality + Context + Persona", detail: "Model-estimated associations, session context, discovered clusters" },
  { icon: Sparkles, label: "Personalized Recommendations", detail: "Hybrid scoring, explained and adaptive to feedback" },
];

const LIMITATIONS = [
  {
    title: "Popularity bias",
    body: "Most recommenders lean on what's already popular — you get more of what everyone already listens to.",
  },
  {
    title: "No explanation",
    body: "\"Because you listened to X\" is usually the whole story. There's no visibility into what actually drove a suggestion.",
  },
  {
    title: "Behavior only",
    body: "Plays and skips are treated as the complete picture, ignoring listening context, personality signal, or discovery intent.",
  },
];

const ADDITIONS = [
  { icon: Radio, title: "Context intelligence", body: "Detects shifts in your current session against your own historical baseline — exploratory, focused, reflective, or routine." },
  { icon: Users2, title: "Persona discovery", body: "Unsupervised clustering over real behavioral features finds listener groups — never hard-coded labels." },
  { icon: Brain, title: "Personality signal", body: "A classical ML model trained on a real personality-music research dataset, evaluated honestly (including where it underperforms)." },
  { icon: ShieldCheck, title: "Full explainability", body: "Every recommendation stores the structured evidence it was scored from, and that evidence is what the explanation is built from — never a generated guess." },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-20">
      <div className="flex flex-col items-start gap-5">
        <Badge tone="accent">College MVP · Research Project</Badge>
        <h1 className="text-5xl sm:text-6xl font-semibold tracking-tight max-w-3xl leading-[1.05]">
          Resona AI
        </h1>
        <p className="text-xl sm:text-2xl max-w-2xl" style={{ color: "var(--text-secondary)" }}>
          Understand people through music.
        </p>
        <p className="max-w-xl" style={{ color: "var(--text-secondary)" }}>
          Resona analyzes real listening behavior to estimate personality-related associations,
          discover listener personas, detect current listening context, and generate
          personalized, explainable music recommendations — all backed by real datasets and
          models, with no fabricated numbers anywhere in the pipeline.
        </p>
        <div className="flex gap-3 pt-2">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-full px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90"
            style={{ background: "var(--accent)" }}
          >
            Open the dashboard <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/about"
            className="inline-flex items-center gap-1.5 rounded-full border px-5 py-2.5 text-sm font-medium transition-colors"
            style={{ borderColor: "var(--border)" }}
          >
            How it works
          </Link>
        </div>
      </div>

      {/* Flow */}
      <div className="mt-20">
        <h2 className="text-sm font-medium uppercase tracking-wide mb-6" style={{ color: "var(--text-muted)" }}>
          From listening data to a recommendation
        </h2>
        <div className="grid gap-3 sm:grid-cols-4">
          {FLOW.map((step, i) => (
            <div key={step.label} className="relative">
              <Card className="h-full">
                <step.icon className="h-5 w-5 mb-3" style={{ color: "var(--accent)" }} />
                <h3 className="font-medium text-sm mb-1">{step.label}</h3>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {step.detail}
                </p>
              </Card>
              {i < FLOW.length - 1 && (
                <ArrowRight
                  className="hidden sm:block absolute top-1/2 -right-2.5 h-4 w-4 -translate-y-1/2 z-10"
                  style={{ color: "var(--text-muted)" }}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Why normal recommenders are limited */}
      <div className="mt-20 grid gap-10 lg:grid-cols-2">
        <div>
          <h2 className="text-2xl font-semibold mb-1">Why typical recommenders fall short</h2>
          <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
            Most systems optimize for one signal — plays — and stop there.
          </p>
          <div className="space-y-4">
            {LIMITATIONS.map((l) => (
              <div key={l.title}>
                <h3 className="font-medium text-sm">{l.title}</h3>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  {l.body}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h2 className="text-2xl font-semibold mb-1">What Resona adds</h2>
          <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
            Four extra layers of signal, each grounded in real models and real data.
          </p>
          <div className="space-y-4">
            {ADDITIONS.map((a) => (
              <div key={a.title} className="flex gap-3">
                <a.icon className="h-4 w-4 mt-0.5 shrink-0" style={{ color: "var(--accent)" }} />
                <div>
                  <h3 className="font-medium text-sm">{a.title}</h3>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    {a.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Research foundation */}
      <Card className="mt-20">
        <div className="flex items-start gap-3">
          <Database className="h-5 w-5 mt-0.5 shrink-0" style={{ color: "var(--accent)" }} />
          <div>
            <h2 className="font-medium mb-1">Built on real research datasets</h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Last.fm 1K (behavioral data, 992 real users), the Beyond the Big Five music-personality
              dataset (279 real research participants), the Million Song Dataset, and DEAM
              (emotion annotations). Every metric on every page of this app is computed from these
              datasets or the models trained on them — see{" "}
              <Link href="/about" className="underline" style={{ color: "var(--accent)" }}>
                Methodology
              </Link>{" "}
              for the full breakdown, including honest limitations.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}

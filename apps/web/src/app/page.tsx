import { Sparkles, Users, Radio, Lightbulb } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { HealthStatus } from "@/components/HealthStatus";

const PIPELINE_STAGES = [
  {
    icon: Sparkles,
    title: "Personality Estimation",
    description:
      "Estimates Big Five trait associations from listening behavior. Model-estimated, not a diagnosis.",
  },
  {
    icon: Users,
    title: "Persona Discovery",
    description: "Clusters listeners into interpretable personas from behavioral and audio features.",
  },
  {
    icon: Radio,
    title: "Context & Mood Detection",
    description: "Identifies current listening context from recent session signals.",
  },
  {
    icon: Lightbulb,
    title: "Explainable Recommendations",
    description: "Generates personalized track recommendations with human-readable reasons.",
  },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <div className="flex flex-col gap-4">
        <Badge>College MVP &middot; Research Project</Badge>
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight max-w-2xl">
          Understand people through music.
        </h1>
        <p className="max-w-xl text-black/60 dark:text-white/60">
          Resona AI is an AI-powered music intelligence system that analyzes listening behavior
          to estimate personality-related traits, discover listener personas, detect listening
          context, and generate explainable recommendations.
        </p>
        <HealthStatus />
      </div>

      <div className="mt-16 grid gap-4 sm:grid-cols-2">
        {PIPELINE_STAGES.map(({ icon: Icon, title, description }) => (
          <Card key={title}>
            <Icon className="h-5 w-5 mb-3 text-black/70 dark:text-white/70" />
            <h2 className="font-medium mb-1">{title}</h2>
            <p className="text-sm text-black/60 dark:text-white/60">{description}</p>
          </Card>
        ))}
      </div>

      <Card className="mt-8">
        <h2 className="font-medium mb-1">Foundation phase</h2>
        <p className="text-sm text-black/60 dark:text-white/60">
          This build establishes the project scaffold: API, database schema, and application
          shell. ML pipeline, dashboard, and recommendation views are implemented in later phases.
        </p>
      </Card>
    </div>
  );
}

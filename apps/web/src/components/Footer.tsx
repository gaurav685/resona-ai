export function Footer() {
  return (
    <footer className="mt-auto border-t py-6" style={{ borderColor: "var(--border)" }}>
      <div
        className="mx-auto max-w-7xl px-6 text-xs space-y-1"
        style={{ color: "var(--text-muted)" }}
      >
        <p>
          Personality outputs are <strong>model-estimated associations</strong> from a research
          dataset of music-listening preferences — not psychological diagnoses, and not derived
          from any individual listener&apos;s Last.fm history.
        </p>
        <p>Resona AI — college research project. All metrics shown come from real, locally-run models.</p>
      </div>
    </footer>
  );
}

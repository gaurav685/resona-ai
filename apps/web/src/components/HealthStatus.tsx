"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

type Status = "checking" | "online" | "offline";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function HealthStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/v1/health`)
      .then((res) => {
        if (!cancelled) setStatus(res.ok ? "online" : "offline");
      })
      .catch(() => {
        if (!cancelled) setStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const config: Record<Status, { icon: React.ReactNode; label: string; color: string }> = {
    checking: {
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      label: "Checking API...",
      color: "text-black/50 dark:text-white/50",
    },
    online: {
      icon: <CheckCircle2 className="h-4 w-4" />,
      label: "API online",
      color: "text-emerald-600 dark:text-emerald-400",
    },
    offline: {
      icon: <XCircle className="h-4 w-4" />,
      label: "API offline — start apps/api",
      color: "text-red-600 dark:text-red-400",
    },
  };

  const { icon, label, color } = config[status];

  return (
    <div className={`flex items-center gap-2 text-sm ${color}`}>
      {icon}
      <span>{label}</span>
    </div>
  );
}

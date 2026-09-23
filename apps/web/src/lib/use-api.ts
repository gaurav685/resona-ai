"use client";

import { useEffect, useState, useCallback } from "react";
import { ApiError } from "./types";

type Status = "idle" | "loading" | "success" | "error";

export function useApi<T>(fetcher: (() => Promise<T>) | null, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [refetchToken, setRefetchToken] = useState(0);

  useEffect(() => {
    if (!fetcher) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: reset to idle when the caller passes a null fetcher (e.g. no user selected yet)
      setStatus("idle");
      return;
    }
    let cancelled = false;
    setStatus("loading");
    setError(null);

    fetcher()
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setStatus("success");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError) {
          setError(err.message);
          setErrorStatus(err.status);
        } else {
          setError("Something went wrong.");
          setErrorStatus(null);
        }
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deps is caller-supplied
  }, [...deps, refetchToken]);

  const refetch = useCallback(() => setRefetchToken((t) => t + 1), []);

  return {
    data,
    isLoading: status === "loading",
    isError: status === "error",
    error,
    errorStatus,
    refetch,
  };
}

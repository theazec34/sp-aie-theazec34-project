"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl } from "../lib/auth";
import { friendlyCatch } from "../lib/errors";

/**
 * Shared async data loader for backoffice list pages.
 * Centralizes loading / error / retry to avoid duplicated useEffect blocks.
 */
export function useAsyncResource<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await loader();
      setData(result);
    } catch (err) {
      setError(friendlyCatch(err, getApiBaseUrl()));
    } finally {
      setLoading(false);
    }
  }, [loader]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, loading, error, reload, setData };
}

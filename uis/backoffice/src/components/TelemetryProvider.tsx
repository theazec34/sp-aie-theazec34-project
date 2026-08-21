"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { getToken } from "../lib/auth";
import {
  telemetry,
  track,
  userIdFromToken,
} from "../services/telemetry";

/**
 * Boots TelemetryService once and emits page_viewed on route changes.
 * Mount only from a client layout wrapper.
 */
export default function TelemetryProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  useEffect(() => {
    telemetry.start();
    const token = getToken();
    if (token) {
      telemetry.setUserId(userIdFromToken(token));
    }
  }, []);

  useEffect(() => {
    if (!pathname) return;
    track("page_viewed", { route: pathname });
  }, [pathname]);

  return <>{children}</>;
}

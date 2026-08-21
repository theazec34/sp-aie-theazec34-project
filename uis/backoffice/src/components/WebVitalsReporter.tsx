"use client";

import { useReportWebVitals } from "next/web-vitals";
import { track } from "../services/telemetry";

/**
 * Sends Core Web Vitals as telemetry events (route in properties).
 */
export default function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    if (typeof window === "undefined") return;
    track("web_vital_recorded", {
      route: window.location.pathname,
      name: metric.name,
      value: Math.round(metric.value * 100) / 100,
      rating: metric.rating,
      id: metric.id,
    });
  });
  return null;
}

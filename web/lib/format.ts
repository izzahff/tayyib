import type { Classification } from "./types";

export function percent(value: number | null, digits = 1): string {
  if (value === null) return "no data";
  return `${(value * 100).toFixed(digits)}%`;
}

export function signedPercent(value: number, digits = 1): string {
  const text = `${(Math.abs(value) * 100).toFixed(digits)}%`;
  return value < 0 ? `-${text}` : `+${text}`;
}

/** Gauge fill from 0 to 1. The limit sits at the halfway mark. */
export function gaugeFill(value: number | null, limit: number): number {
  if (value === null || limit <= 0) return 0;
  return Math.min(Math.max(value / (limit * 2), 0), 1);
}

/** A value equal to the limit passes, matching the Python screen. */
export function passesLimit(value: number | null, limit: number): boolean | null {
  if (value === null) return null;
  return value <= limit;
}

export function verdictLabel(classification: Classification): string {
  if (classification === "compliant") return "Compliant";
  if (classification === "non-compliant") return "Not compliant";
  return "Not screened";
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "not finished";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "unknown";
  const text = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(date);
  return `${text} UTC`;
}

export function formatDuration(start: string, end: string | null): string {
  if (!end) return "still running or never finished";
  const seconds = Math.max(
    0,
    Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000),
  );
  if (seconds < 60) return `${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ${seconds % 60} s`;
}

import { describe, expect, it } from "vitest";
import { gaugeFill, passesLimit, percent, signedPercent, formatDuration } from "./format";

describe("format helpers", () => {
  it("formats ratios and missing values", () => {
    expect(percent(0.184)).toBe("18.4%");
    expect(percent(null)).toBe("no data");
  });

  it("signs returns", () => {
    expect(signedPercent(0.2)).toBe("+20.0%");
    expect(signedPercent(-0.05)).toBe("-5.0%");
  });

  it("puts the limit at the halfway mark of the gauge", () => {
    expect(gaugeFill(0.3, 0.3)).toBe(0.5);
    expect(gaugeFill(0.9, 0.3)).toBe(1);
    expect(gaugeFill(null, 0.3)).toBe(0);
  });

  it("treats a value equal to the limit as a pass", () => {
    expect(passesLimit(0.3, 0.3)).toBe(true);
    expect(passesLimit(0.31, 0.3)).toBe(false);
    expect(passesLimit(null, 0.3)).toBeNull();
  });

  it("describes how long a run took", () => {
    expect(formatDuration("2026-11-06T00:00:00Z", "2026-11-06T00:02:05Z")).toBe("2 min 5 s");
    expect(formatDuration("2026-11-06T00:00:00Z", null)).toContain("never finished");
  });
});

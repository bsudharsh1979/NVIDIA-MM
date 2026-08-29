import { EVIDENCE } from "../lib/evidence";
import { describe, expect, it } from "vitest";

describe("evidence labels", () => {
  it("never aliases simulation to actual", () => {
    expect(EVIDENCE.SIMULATED_RESULT.label).toContain("SIMULATION");
    expect(EVIDENCE.ACTUAL_RUN.label).toContain("ACTUAL");
    expect(EVIDENCE.SIMULATED_RESULT.label).not.toContain("ACTUAL");
  });
});

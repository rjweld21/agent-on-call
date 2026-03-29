import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  VerbositySlider,
  VERBOSITY_LEVELS,
  DEFAULT_VERBOSITY,
  getVerbosityPrompt,
} from "./VerbositySlider";
import { SettingsProvider } from "@/lib/settings-context";

function renderWithProvider(ui: React.ReactElement) {
  return render(<SettingsProvider>{ui}</SettingsProvider>);
}

describe("VerbositySlider", () => {
  it("renders a range input with min 1 and max 5", () => {
    renderWithProvider(<VerbositySlider />);
    const slider = screen.getByTestId("verbosity-slider") as HTMLInputElement;
    expect(slider).toBeInTheDocument();
    expect(slider.type).toBe("range");
    expect(slider.min).toBe("1");
    expect(slider.max).toBe("5");
  });

  it("defaults to level 3 (Balanced)", () => {
    renderWithProvider(<VerbositySlider />);
    const slider = screen.getByTestId("verbosity-slider") as HTMLInputElement;
    expect(slider.value).toBe(String(DEFAULT_VERBOSITY));
    expect(screen.getByTestId("verbosity-level-label").textContent).toContain(
      "Balanced"
    );
  });

  it("shows Concise label at left and Wordy label at right", () => {
    renderWithProvider(<VerbositySlider />);
    expect(screen.getByText("Concise")).toBeInTheDocument();
    expect(screen.getByText("Wordy")).toBeInTheDocument();
  });

  it("updates level when slider changes", () => {
    renderWithProvider(<VerbositySlider />);
    const slider = screen.getByTestId("verbosity-slider") as HTMLInputElement;
    fireEvent.change(slider, { target: { value: "5" } });
    expect(slider.value).toBe("5");
    expect(screen.getByTestId("verbosity-level-label").textContent).toContain(
      "Verbose"
    );
  });

  it("shows tooltip trigger with explanation text", () => {
    renderWithProvider(<VerbositySlider />);
    const tooltip = screen.getByTestId("verbosity-tooltip-trigger");
    expect(tooltip).toBeInTheDocument();
    expect(tooltip.title).toContain("Level 1 is extremely concise");
    expect(tooltip.title).toContain("Level 5 gives full explanations");
  });

  it("has 5 defined verbosity levels", () => {
    expect(VERBOSITY_LEVELS).toHaveLength(5);
    expect(VERBOSITY_LEVELS[0].level).toBe(1);
    expect(VERBOSITY_LEVELS[4].level).toBe(5);
  });

  it("has a label for accessibility", () => {
    renderWithProvider(<VerbositySlider />);
    expect(screen.getByLabelText("Verbosity")).toBeInTheDocument();
  });
});

describe("getVerbosityPrompt", () => {
  it("returns correct prompt for each level", () => {
    for (const entry of VERBOSITY_LEVELS) {
      expect(getVerbosityPrompt(entry.level)).toBe(entry.prompt);
    }
  });

  it("returns balanced prompt for invalid level", () => {
    expect(getVerbosityPrompt(99)).toBe(VERBOSITY_LEVELS[2].prompt);
    expect(getVerbosityPrompt(0)).toBe(VERBOSITY_LEVELS[2].prompt);
  });
});

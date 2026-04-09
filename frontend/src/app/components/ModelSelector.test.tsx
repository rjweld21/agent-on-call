import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelSelector, ANTHROPIC_MODELS, DEFAULT_MODEL } from "./ModelSelector";
import { SettingsProvider } from "@/lib/settings-context";

function renderWithProvider(ui: React.ReactElement) {
  return render(<SettingsProvider>{ui}</SettingsProvider>);
}

describe("ModelSelector", () => {
  it("renders a select element", () => {
    renderWithProvider(<ModelSelector />);
    expect(screen.getByTestId("model-selector")).toBeInTheDocument();
  });

  it("renders all three Anthropic model options", () => {
    renderWithProvider(<ModelSelector />);
    const select = screen.getByTestId("model-selector") as HTMLSelectElement;
    const options = Array.from(select.options);
    expect(options).toHaveLength(3);
    expect(options.map((o) => o.text)).toEqual([
      "Claude Haiku 4.5",
      "Claude Sonnet 4.5",
      "Claude Opus 4",
    ]);
  });

  it("has correct model values on options", () => {
    renderWithProvider(<ModelSelector />);
    const select = screen.getByTestId("model-selector") as HTMLSelectElement;
    const options = Array.from(select.options);
    expect(options.map((o) => o.value)).toEqual(
      ANTHROPIC_MODELS.map((m) => m.value)
    );
  });

  it("defaults to Claude Sonnet 4.5", () => {
    renderWithProvider(<ModelSelector />);
    const select = screen.getByTestId("model-selector") as HTMLSelectElement;
    expect(select.value).toBe(DEFAULT_MODEL);
  });

  it("updates selection on change", async () => {
    const user = userEvent.setup();
    renderWithProvider(<ModelSelector />);
    const select = screen.getByTestId("model-selector") as HTMLSelectElement;

    await user.selectOptions(select, "claude-opus-4-20250514");
    expect(select.value).toBe("claude-opus-4-20250514");
  });

  it("renders a label for accessibility", () => {
    renderWithProvider(<ModelSelector />);
    expect(screen.getByLabelText("Anthropic Model")).toBeInTheDocument();
  });
});

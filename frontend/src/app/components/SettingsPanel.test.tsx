import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsPanel } from "./SettingsPanel";
import { SettingsProvider } from "@/lib/settings-context";

function renderWithProvider(ui: React.ReactElement) {
  return render(<SettingsProvider>{ui}</SettingsProvider>);
}

describe("SettingsPanel", () => {
  it("renders panel content when isOpen is true", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("does not render panel content when isOpen is false", () => {
    renderWithProvider(<SettingsPanel isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    const onClose = vi.fn();
    renderWithProvider(<SettingsPanel isOpen={true} onClose={onClose} />);
    await userEvent.click(screen.getByLabelText("Close settings"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when backdrop is clicked", async () => {
    const onClose = vi.fn();
    renderWithProvider(<SettingsPanel isOpen={true} onClose={onClose} />);
    await userEvent.click(screen.getByTestId("settings-backdrop"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Escape key is pressed", () => {
    const onClose = vi.fn();
    renderWithProvider(<SettingsPanel isOpen={true} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not call onClose on Escape when panel is closed", () => {
    const onClose = vi.fn();
    renderWithProvider(<SettingsPanel isOpen={false} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("renders section titles", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText("Voice")).toBeInTheDocument();
  });

  it("renders placeholder text only for sections without components", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    const placeholders = screen.getAllByText("No settings available yet.");
    // Model has ModelSelector, Voice has VerbositySlider, only General has placeholder
    expect(placeholders.length).toBe(1);
  });

  it("renders ModelSelector in the Model section", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("model-selector")).toBeInTheDocument();
  });

  it("renders VerbositySlider in the Voice section", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("verbosity-slider")).toBeInTheDocument();
  });

  it("has correct aria-label on the panel", () => {
    renderWithProvider(<SettingsPanel isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByRole("dialog")).toHaveAttribute(
      "aria-label",
      "Settings panel",
    );
  });
});

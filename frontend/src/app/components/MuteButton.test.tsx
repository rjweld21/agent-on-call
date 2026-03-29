import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MuteButton } from "./MuteButton";

// Mock @livekit/components-react
const mockSetMicrophoneEnabled = vi.fn();
let mockIsMicrophoneEnabled = true;

vi.mock("@livekit/components-react", () => ({
  useLocalParticipant: () => ({
    localParticipant: {
      setMicrophoneEnabled: mockSetMicrophoneEnabled,
      isMicrophoneEnabled: mockIsMicrophoneEnabled,
    },
    isMicrophoneEnabled: mockIsMicrophoneEnabled,
  }),
}));

describe("MuteButton", () => {
  beforeEach(() => {
    mockIsMicrophoneEnabled = true;
    mockSetMicrophoneEnabled.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with unmuted state by default", () => {
    render(<MuteButton />);
    const button = screen.getByRole("button", { name: /mute microphone/i });
    expect(button).toBeInTheDocument();
  });

  it("shows correct aria-label when unmuted", () => {
    mockIsMicrophoneEnabled = true;
    render(<MuteButton />);
    expect(screen.getByRole("button", { name: "Mute microphone (M)" })).toBeInTheDocument();
  });

  it("shows correct aria-label when muted", () => {
    mockIsMicrophoneEnabled = false;
    render(<MuteButton />);
    expect(screen.getByRole("button", { name: "Unmute microphone (M)" })).toBeInTheDocument();
  });

  it("calls setMicrophoneEnabled(false) when clicking while unmuted", async () => {
    mockIsMicrophoneEnabled = true;
    render(<MuteButton />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockSetMicrophoneEnabled).toHaveBeenCalledWith(false);
  });

  it("calls setMicrophoneEnabled(true) when clicking while muted", async () => {
    mockIsMicrophoneEnabled = false;
    render(<MuteButton />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockSetMicrophoneEnabled).toHaveBeenCalledWith(true);
  });

  it("toggles mute on M key press", () => {
    mockIsMicrophoneEnabled = true;
    render(<MuteButton />);
    fireEvent.keyDown(document, { key: "m" });
    expect(mockSetMicrophoneEnabled).toHaveBeenCalledWith(false);
  });

  it("toggles mute on uppercase M key press", () => {
    mockIsMicrophoneEnabled = true;
    render(<MuteButton />);
    fireEvent.keyDown(document, { key: "M" });
    expect(mockSetMicrophoneEnabled).toHaveBeenCalledWith(false);
  });

  it("does NOT toggle mute when M is pressed while typing in an input", () => {
    mockIsMicrophoneEnabled = true;
    render(
      <div>
        <input data-testid="text-input" />
        <MuteButton />
      </div>,
    );
    const input = screen.getByTestId("text-input");
    input.focus();
    fireEvent.keyDown(document, { key: "m" });
    expect(mockSetMicrophoneEnabled).not.toHaveBeenCalled();
  });

  it("does NOT toggle mute when M is pressed while typing in a textarea", () => {
    mockIsMicrophoneEnabled = true;
    render(
      <div>
        <textarea data-testid="text-area" />
        <MuteButton />
      </div>,
    );
    const textarea = screen.getByTestId("text-area");
    textarea.focus();
    fireEvent.keyDown(document, { key: "m" });
    expect(mockSetMicrophoneEnabled).not.toHaveBeenCalled();
  });

  it("has green border styling when unmuted", () => {
    mockIsMicrophoneEnabled = true;
    render(<MuteButton />);
    const button = screen.getByRole("button");
    // jsdom normalizes hex to rgb
    expect(button.style.borderColor).toMatch(/22c55e|rgb\(34,\s*197,\s*94\)/);
  });

  it("has red border styling when muted", () => {
    mockIsMicrophoneEnabled = false;
    render(<MuteButton />);
    const button = screen.getByRole("button");
    expect(button.style.borderColor).toMatch(/ef4444|rgb\(239,\s*68,\s*68\)/);
  });
});

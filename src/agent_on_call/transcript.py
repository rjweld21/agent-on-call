"""Transcript saving — captures session transcript to JSON."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class TranscriptEntry:
    """A single transcript entry (speech, tool call, or tool result)."""

    timestamp: str
    speaker: str
    content: str
    entry_type: str  # "speech", "tool_call", "tool_result"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "speaker": self.speaker,
            "content": self.content,
            "type": self.entry_type,
        }


@dataclass
class SessionTranscript:
    """Tracks and saves a session transcript to JSON.

    Usage:
        transcript = SessionTranscript(session_id="room-abc")
        transcript.add_entry(speaker="user", content="Hello", entry_type="speech")
        transcript.add_entry(speaker="agent", content="Hi there", entry_type="speech")
        transcript.end_session()
        transcript.save("/path/to/transcripts")
    """

    session_id: str
    entries: list[TranscriptEntry] = field(default_factory=list)
    participants: list[dict[str, str]] = field(default_factory=list)
    _started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _ended_at: datetime | None = field(default=None)

    def add_entry(
        self,
        speaker: str,
        content: str,
        entry_type: str = "speech",
        timestamp: str | None = None,
    ) -> None:
        """Add a transcript entry.

        Args:
            speaker: Who spoke ("user", "agent", or sub-agent name).
            content: The text content.
            entry_type: "speech", "tool_call", or "tool_result".
            timestamp: ISO 8601 timestamp (auto-generated if None).
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.entries.append(
            TranscriptEntry(
                timestamp=timestamp,
                speaker=speaker,
                content=content,
                entry_type=entry_type,
            )
        )

    def add_participant(self, identity: str, name: str) -> None:
        """Track a session participant."""
        participant = {"identity": identity, "name": name}
        if participant not in self.participants:
            self.participants.append(participant)

    def end_session(self) -> None:
        """Mark the session as ended."""
        self._ended_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Serialize the transcript to a dictionary."""
        ended = self._ended_at or datetime.now(timezone.utc)
        duration = (ended - self._started_at).total_seconds()
        return {
            "session_id": self.session_id,
            "started_at": self._started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ended_at": ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_seconds": round(duration, 1),
            "participants": list(self.participants),
            "entries": [e.to_dict() for e in self.entries],
        }

    def to_json(self) -> str:
        """Serialize the transcript to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def get_filename(self) -> str:
        """Generate a filename based on session start time."""
        return self._started_at.strftime("%Y-%m-%d-%H%M%S") + ".json"

    def save(self, directory: str) -> str:
        """Save the transcript to a JSON file.

        Args:
            directory: Directory to save the transcript in.

        Returns:
            The full path of the saved file.
        """
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, self.get_filename())
        with open(filepath, "w") as f:
            f.write(self.to_json())
        logger.info(
            "Transcript saved: %s (%d entries, %.1fs)",
            filepath,
            len(self.entries),
            self.to_dict()["duration_seconds"],
        )
        return filepath

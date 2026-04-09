"""Tests for transcript saving module."""

import json
import os
import tempfile


class TestTranscriptEntry:
    def test_create_entry(self):
        from agent_on_call.transcript import TranscriptEntry

        entry = TranscriptEntry(
            timestamp="2026-03-25T10:00:00Z",
            speaker="user",
            content="Hello agent",
            entry_type="speech",
        )
        assert entry.timestamp == "2026-03-25T10:00:00Z"
        assert entry.speaker == "user"
        assert entry.content == "Hello agent"
        assert entry.entry_type == "speech"

    def test_entry_to_dict(self):
        from agent_on_call.transcript import TranscriptEntry

        entry = TranscriptEntry(
            timestamp="2026-03-25T10:00:00Z",
            speaker="agent",
            content="How can I help?",
            entry_type="speech",
        )
        d = entry.to_dict()
        assert d == {
            "timestamp": "2026-03-25T10:00:00Z",
            "speaker": "agent",
            "content": "How can I help?",
            "type": "speech",
        }

    def test_entry_types(self):
        from agent_on_call.transcript import TranscriptEntry

        for entry_type in ["speech", "tool_call", "tool_result"]:
            entry = TranscriptEntry(
                timestamp="2026-03-25T10:00:00Z",
                speaker="agent",
                content="test",
                entry_type=entry_type,
            )
            assert entry.entry_type == entry_type


class TestSessionTranscript:
    def test_create_session_transcript(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test-session-123")
        assert transcript.session_id == "test-session-123"
        assert len(transcript.entries) == 0

    def test_add_entry(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_entry(
            speaker="user",
            content="Hello",
            entry_type="speech",
        )
        assert len(transcript.entries) == 1
        assert transcript.entries[0].speaker == "user"
        assert transcript.entries[0].content == "Hello"
        # Timestamp should be auto-generated
        assert transcript.entries[0].timestamp is not None

    def test_add_multiple_entries(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_entry(speaker="user", content="Hi", entry_type="speech")
        transcript.add_entry(speaker="agent", content="Hello", entry_type="speech")
        transcript.add_entry(speaker="agent", content="git status", entry_type="tool_call")
        assert len(transcript.entries) == 3

    def test_to_dict_includes_metadata(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test-123")
        transcript.add_entry(speaker="user", content="Test", entry_type="speech")
        transcript.end_session()

        d = transcript.to_dict()
        assert d["session_id"] == "test-123"
        assert "started_at" in d
        assert "ended_at" in d
        assert "duration_seconds" in d
        assert isinstance(d["entries"], list)
        assert len(d["entries"]) == 1

    def test_to_json_string(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_entry(speaker="user", content="Hello", entry_type="speech")
        transcript.end_session()

        json_str = transcript.to_json()
        parsed = json.loads(json_str)
        assert parsed["session_id"] == "test"
        assert len(parsed["entries"]) == 1

    def test_duration_calculation(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.end_session()
        d = transcript.to_dict()
        assert d["duration_seconds"] >= 0

    def test_file_naming(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        filename = transcript.get_filename()
        assert filename.endswith(".json")
        # Should contain date pattern
        assert "-" in filename

    def test_save_to_directory(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_entry(speaker="user", content="Hello", entry_type="speech")
        transcript.add_entry(speaker="agent", content="Hi there", entry_type="speech")
        transcript.end_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = transcript.save(tmpdir)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                data = json.load(f)
            assert data["session_id"] == "test"
            assert len(data["entries"]) == 2

    def test_save_creates_directory_if_missing(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_entry(speaker="user", content="Hi", entry_type="speech")
        transcript.end_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "transcripts", "deep")
            filepath = transcript.save(nested)
            assert os.path.exists(filepath)

    def test_empty_transcript_still_saves(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="empty")
        transcript.end_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = transcript.save(tmpdir)
            assert os.path.exists(filepath)
            with open(filepath) as f:
                data = json.load(f)
            assert data["session_id"] == "empty"
            assert len(data["entries"]) == 0

    def test_participants_tracking(self):
        from agent_on_call.transcript import SessionTranscript

        transcript = SessionTranscript(session_id="test")
        transcript.add_participant("user-1", "User")
        transcript.add_participant("agent-1", "Orchestrator")

        d = transcript.to_dict()
        assert len(d["participants"]) == 2
        assert {"identity": "user-1", "name": "User"} in d["participants"]

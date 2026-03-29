"""Tests for code analysis tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_on_call.code_analysis import (
    CodeAnalysisTool,
    detect_stack,
    format_tree_output,
    format_grep_output,
)


class TestDetectStack:
    """Test framework/stack detection from file listings."""

    def test_detects_python_pyproject(self):
        files = "pyproject.toml\nsrc/\ntests/"
        stack = detect_stack(files)
        assert "python" in stack.lower()

    def test_detects_python_requirements(self):
        files = "requirements.txt\napp.py"
        stack = detect_stack(files)
        assert "python" in stack.lower()

    def test_detects_node_packagejson(self):
        files = "package.json\nsrc/\nnode_modules/"
        stack = detect_stack(files)
        assert "node" in stack.lower() or "javascript" in stack.lower() or "typescript" in stack.lower()

    def test_detects_rust_cargo(self):
        files = "Cargo.toml\nsrc/main.rs"
        stack = detect_stack(files)
        assert "rust" in stack.lower()

    def test_detects_go_module(self):
        files = "go.mod\ngo.sum\nmain.go"
        stack = detect_stack(files)
        assert "go" in stack.lower()

    def test_detects_multiple_stacks(self):
        files = "pyproject.toml\npackage.json\nDockerfile"
        stack = detect_stack(files)
        assert "python" in stack.lower()
        assert "node" in stack.lower() or "javascript" in stack.lower() or "typescript" in stack.lower()

    def test_unknown_stack(self):
        files = "README.md\nLICENSE"
        stack = detect_stack(files)
        assert "unknown" in stack.lower() or stack == ""


class TestFormatTreeOutput:
    """Test tree output formatting."""

    def test_formats_basic_tree(self):
        raw = "src/\nsrc/main.py\nsrc/utils.py\ntests/\ntests/test_main.py"
        result = format_tree_output(raw, depth=3)
        assert "src/" in result
        assert "main.py" in result

    def test_handles_empty_output(self):
        result = format_tree_output("", depth=3)
        assert result == "" or "empty" in result.lower() or "no files" in result.lower()

    def test_truncates_long_output(self):
        lines = [f"file_{i}.py" for i in range(500)]
        raw = "\n".join(lines)
        result = format_tree_output(raw, depth=3)
        assert len(result) < len(raw)  # Should be truncated
        assert "truncated" in result.lower() or len(result.split("\n")) <= 200


class TestFormatGrepOutput:
    """Test grep output formatting."""

    def test_formats_grep_results(self):
        raw = "src/main.py:10:def main():\nsrc/utils.py:5:import os"
        result = format_grep_output(raw)
        assert "main.py" in result
        assert "def main" in result

    def test_handles_empty_output(self):
        result = format_grep_output("")
        assert result == "" or "no matches" in result.lower()

    def test_truncates_many_matches(self):
        lines = [f"file.py:{i}:match line {i}" for i in range(200)]
        raw = "\n".join(lines)
        result = format_grep_output(raw)
        # Should be limited
        assert len(result.split("\n")) <= 120 or "truncated" in result.lower()


class TestCodeAnalysisTool:
    """Test the CodeAnalysisTool integration."""

    @pytest.mark.asyncio
    async def test_analyze_returns_structure(self):
        mock_ws = MagicMock()
        # git ls-files for tree
        mock_ws.exec_command.side_effect = [
            (0, "src/main.py\nsrc/utils.py\ntests/test_main.py\npyproject.toml\npackage.json", ""),  # git ls-files
        ]
        tool = CodeAnalysisTool(mock_ws)
        result = await tool.analyze(path="/workspace")
        assert "src/" in result or "main.py" in result
        assert "python" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_with_query_runs_grep(self):
        mock_ws = MagicMock()
        mock_ws.exec_command.side_effect = [
            (0, "src/main.py\npyproject.toml", ""),  # git ls-files
            (0, "src/main.py:10:def hello():", ""),  # grep
        ]
        tool = CodeAnalysisTool(mock_ws)
        result = await tool.analyze(path="/workspace", query="def hello")
        assert "main.py" in result
        assert "def hello" in result

    @pytest.mark.asyncio
    async def test_analyze_non_git_falls_back(self):
        mock_ws = MagicMock()
        mock_ws.exec_command.side_effect = [
            (128, "", "fatal: not a git repository"),  # git ls-files fails
            (0, "file1.py\nfile2.py\ndir1/", ""),  # find fallback
        ]
        tool = CodeAnalysisTool(mock_ws)
        result = await tool.analyze(path="/workspace")
        assert "file1.py" in result or "file2.py" in result

    @pytest.mark.asyncio
    async def test_analyze_truncates_output(self):
        mock_ws = MagicMock()
        large_listing = "\n".join([f"path/to/file_{i}.py" for i in range(1000)])
        mock_ws.exec_command.return_value = (0, large_listing, "")
        tool = CodeAnalysisTool(mock_ws)
        result = await tool.analyze(path="/workspace")
        assert len(result) <= 16_000  # ~15KB budget

    @pytest.mark.asyncio
    async def test_analyze_handles_exec_error(self):
        mock_ws = MagicMock()
        mock_ws.exec_command.side_effect = RuntimeError("No active workspace")
        tool = CodeAnalysisTool(mock_ws)
        result = await tool.analyze(path="/workspace")
        assert "error" in result.lower()

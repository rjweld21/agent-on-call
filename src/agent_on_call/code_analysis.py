"""Code analysis tool for the agent — project structure, grep, and stack detection."""

import logging

logger = logging.getLogger(__name__)

MAX_OUTPUT_BYTES = 15_000  # ~15KB context budget for analysis output
MAX_TREE_LINES = 150
MAX_GREP_LINES = 100

# Known project config files → stack/framework
STACK_INDICATORS = [
    ("pyproject.toml", "Python"),
    ("setup.py", "Python"),
    ("requirements.txt", "Python"),
    ("Pipfile", "Python"),
    ("package.json", "Node.js / JavaScript / TypeScript"),
    ("tsconfig.json", "TypeScript"),
    ("Cargo.toml", "Rust"),
    ("go.mod", "Go"),
    ("pom.xml", "Java (Maven)"),
    ("build.gradle", "Java/Kotlin (Gradle)"),
    ("Gemfile", "Ruby"),
    ("composer.json", "PHP"),
    ("Makefile", "Make-based build"),
    ("Dockerfile", "Docker"),
    ("docker-compose.yml", "Docker Compose"),
    ("docker-compose.yaml", "Docker Compose"),
    (".github/workflows", "GitHub Actions CI"),
]


def detect_stack(file_listing: str) -> str:
    """Detect project stack/framework from a file listing.

    Args:
        file_listing: Newline-separated file paths from the project root.

    Returns:
        Human-readable string describing detected stacks, or empty string if unknown.
    """
    if not file_listing.strip():
        return ""

    detected = []
    listing_lower = file_listing.lower()
    seen = set()

    for indicator, stack_name in STACK_INDICATORS:
        if indicator.lower() in listing_lower and stack_name not in seen:
            detected.append(stack_name)
            seen.add(stack_name)

    if not detected:
        return "Unknown — no recognized project configuration files found"

    return ", ".join(detected)


def format_tree_output(raw: str, depth: int = 3) -> str:
    """Format a file listing into a readable tree structure.

    Args:
        raw: Newline-separated file paths.
        depth: Maximum directory depth to show.

    Returns:
        Formatted tree string, truncated if too long.
    """
    if not raw.strip():
        return "No files found."

    lines = raw.strip().split("\n")

    # Filter by depth
    filtered = []
    for line in lines:
        parts = line.strip().split("/")
        if len(parts) <= depth + 1:  # +1 because root level counts
            filtered.append(line.strip())

    if len(filtered) > MAX_TREE_LINES:
        result_lines = filtered[:MAX_TREE_LINES]
        result_lines.append(f"\n... [truncated — {len(filtered)} files total, showing first {MAX_TREE_LINES}]")
        return "\n".join(result_lines)

    return "\n".join(filtered)


def format_grep_output(raw: str) -> str:
    """Format grep results for LLM consumption.

    Args:
        raw: Raw grep output (file:line:content format).

    Returns:
        Formatted grep results, truncated if too many matches.
    """
    if not raw.strip():
        return "No matches found."

    lines = raw.strip().split("\n")

    if len(lines) > MAX_GREP_LINES:
        result_lines = lines[:MAX_GREP_LINES]
        result_lines.append(f"\n... [truncated — {len(lines)} matches total, showing first {MAX_GREP_LINES}]")
        return "\n".join(result_lines)

    return "\n".join(lines)


class CodeAnalysisTool:
    """Provides codebase analysis capabilities for the agent.

    Delegates to WorkspaceManager.exec_command() for shell commands
    within the workspace container.
    """

    def __init__(self, workspace) -> None:
        """Initialize with a WorkspaceManager instance.

        Args:
            workspace: WorkspaceManager for executing commands in the workspace.
        """
        self._workspace = workspace

    async def analyze(
        self,
        path: str = "/workspace",
        query: str = "",
        depth: int = 3,
    ) -> str:
        """Analyze a codebase directory.

        Args:
            path: Directory to analyze (default: /workspace).
            query: Optional grep pattern to search for.
            depth: Tree depth limit (default: 3).

        Returns:
            Structured analysis summary.
        """
        sections = []

        # 1. Get file listing (prefer git ls-files for .gitignore respect)
        try:
            file_listing = await self._get_file_listing(path)
        except RuntimeError as e:
            return f"Error: {e}"

        # 2. Detect stack
        stack = detect_stack(file_listing)
        if stack:
            sections.append(f"**Project Type:** {stack}")

        # 3. Format tree
        tree = format_tree_output(file_listing, depth=depth)
        sections.append(f"**Project Structure:**\n```\n{tree}\n```")

        # 4. File statistics
        stats = self._compute_file_stats(file_listing)
        if stats:
            sections.append(f"**File Statistics:**\n{stats}")

        # 5. Grep if query provided
        if query:
            try:
                grep_result = await self._grep(path, query)
                sections.append(f"**Search Results for `{query}`:**\n```\n{grep_result}\n```")
            except RuntimeError:
                sections.append(f"**Search Results for `{query}`:** Error running grep.")

        result = "\n\n".join(sections)

        # Truncate if over budget
        if len(result.encode("utf-8")) > MAX_OUTPUT_BYTES:
            truncated = result.encode("utf-8")[:MAX_OUTPUT_BYTES].decode("utf-8", errors="ignore")
            result = truncated + f"\n\n[Truncated — output exceeded {MAX_OUTPUT_BYTES:,} byte limit]"

        return result

    async def _get_file_listing(self, path: str) -> str:
        """Get file listing, preferring git ls-files for .gitignore support."""
        try:
            exit_code, stdout, stderr = self._workspace.exec_command(f"git -C {path} ls-files", timeout=15)
            if exit_code == 0 and stdout.strip():
                return stdout.strip()
        except RuntimeError:
            raise

        # Fallback: find command for non-git directories
        exit_code, stdout, stderr = self._workspace.exec_command(
            f"find {path} -maxdepth 4 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -type f",
            timeout=15,
        )
        if exit_code == 0:
            # Strip the path prefix for cleaner output
            lines = stdout.strip().split("\n")
            cleaned = [line.replace(f"{path}/", "", 1) for line in lines if line.strip()]
            return "\n".join(cleaned)

        raise RuntimeError(f"Failed to list files in {path}")

    async def _grep(self, path: str, query: str) -> str:
        """Search for a pattern in files."""
        # Escape single quotes in query
        safe_query = query.replace("'", "'\\''")
        exit_code, stdout, stderr = self._workspace.exec_command(
            f"grep -rn --include='*.py' --include='*.js' --include='*.ts' --include='*.tsx' "
            f"--include='*.go' --include='*.rs' --include='*.java' --include='*.rb' "
            f"--include='*.yaml' --include='*.yml' --include='*.json' --include='*.toml' "
            f"'{safe_query}' {path}",
            timeout=15,
        )
        if exit_code == 0:
            # Strip path prefix
            result = stdout.strip().replace(f"{path}/", "")
            return format_grep_output(result)
        elif exit_code == 1:
            # grep returns 1 when no matches found
            return "No matches found."
        else:
            return f"Grep failed: {stderr or stdout}"

    def _compute_file_stats(self, file_listing: str) -> str:
        """Compute file extension statistics from a listing."""
        if not file_listing.strip():
            return ""

        ext_counts: dict[str, int] = {}
        total = 0
        for line in file_listing.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            total += 1
            # Get extension
            if "." in line.split("/")[-1]:
                ext = "." + line.split("/")[-1].rsplit(".", 1)[-1]
            else:
                ext = "(no extension)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        if not ext_counts:
            return ""

        # Sort by count descending
        sorted_exts = sorted(ext_counts.items(), key=lambda x: -x[1])
        lines = [f"Total files: {total}"]
        for ext, count in sorted_exts[:15]:  # Top 15 extensions
            lines.append(f"  {ext}: {count}")

        return "\n".join(lines)

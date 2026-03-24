"""Workspace container management via Docker SDK."""

import docker
from docker.models.containers import Container


class WorkspaceManager:
    def __init__(self, image: str = "aoc-workspace-dev"):
        self._client = docker.from_env()
        self._image = image
        self._active_container: Container | None = None
        self._workspace_name: str | None = None

    def create_workspace(self, name: str) -> str:
        """Create and start a new workspace container with a persistent volume."""
        volume_name = f"aoc-workspace-{name}"
        container = self._client.containers.run(
            self._image,
            name=f"aoc-ws-{name}",
            volumes={volume_name: {"bind": "/workspace", "mode": "rw"}},
            detach=True,
            remove=False,
        )
        self._active_container = container
        self._workspace_name = name
        return container.id

    def exec_command(self, command: str, workdir: str = "/workspace") -> tuple[int, str]:
        """Execute a command in the active workspace container. Returns (exit_code, output)."""
        if not self._active_container:
            raise RuntimeError("No active workspace. Create one first.")

        # Refresh container state
        self._active_container.reload()
        if self._active_container.status != "running":
            self._active_container.start()
            self._active_container.reload()

        result = self._active_container.exec_run(
            cmd=["sh", "-c", command],
            workdir=workdir,
            demux=True,
        )
        stdout = result.output[0].decode("utf-8") if result.output[0] else ""
        stderr = result.output[1].decode("utf-8") if result.output[1] else ""
        output = stdout + stderr
        return result.exit_code, output.strip()

    def read_file(self, path: str) -> str:
        """Read a file from the workspace container."""
        exit_code, output = self.exec_command(f"cat {path}")
        if exit_code != 0:
            raise FileNotFoundError(f"Could not read {path}: {output}")
        return output

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file in the workspace container."""
        # Use heredoc to handle multi-line content
        exit_code, output = self.exec_command(f"cat > {path} << 'AOCEOF'\n{content}\nAOCEOF")
        if exit_code != 0:
            raise IOError(f"Could not write {path}: {output}")
        return f"Written to {path}"

    def list_files(self, path: str = "/workspace") -> str:
        """List files in a directory in the workspace."""
        exit_code, output = self.exec_command(f"ls -la {path}")
        if exit_code != 0:
            return f"Could not list {path}: {output}"
        return output

    def get_active_workspace(self) -> str | None:
        """Return the name of the active workspace, or None."""
        return self._workspace_name

    def stop_workspace(self) -> None:
        """Stop the active workspace container."""
        if self._active_container:
            self._active_container.stop()
            self._active_container = None
            self._workspace_name = None

    def delete_workspace(self, name: str) -> None:
        """Delete a workspace container and its volume."""
        try:
            container = self._client.containers.get(f"aoc-ws-{name}")
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
        try:
            self._client.volumes.get(f"aoc-workspace-{name}").remove()
        except docker.errors.NotFound:
            pass

    def list_workspaces(self) -> list[dict]:
        """List all workspace containers."""
        containers = self._client.containers.list(all=True, filters={"name": "aoc-ws-"})
        return [
            {
                "name": c.name.replace("aoc-ws-", ""),
                "status": c.status,
                "id": c.short_id,
            }
            for c in containers
        ]

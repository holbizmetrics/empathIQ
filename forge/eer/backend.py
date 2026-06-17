"""LLM backends. Real runs go through the `claude` CLI (no API key setup needed,
which is the point for a first-time builder). The mock backend is deterministic so
tests and dry-runs work fully offline."""
from __future__ import annotations
import hashlib
import shutil
import subprocess


class Backend:
    name = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class ClaudeCLIBackend(Backend):
    name = "claude-cli"

    def __init__(self, model: str | None = None, timeout: int = 120) -> None:
        if not shutil.which("claude"):
            raise RuntimeError("`claude` CLI not found on PATH; use --mock instead")
        self.model = model
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        cmd = ["claude", "-p", user]
        if system:
            cmd += ["--append-system-prompt", system]
        if self.model:
            cmd += ["--model", self.model]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"claude CLI failed ({proc.returncode}): {proc.stderr.strip()}")
        return proc.stdout.strip()


class MockBackend(Backend):
    """Deterministic stand-in: echoes a short, hashed marker per block instruction.
    Same input -> same output, so A/B structure can be tested without API calls."""
    name = "mock"

    def complete(self, system: str, user: str) -> str:
        h = hashlib.sha256((system + "\x00" + user).encode()).hexdigest()[:8]
        head = (system.splitlines()[0] if system else "block")[:60]
        return f"[mock:{h}] {head} -> processed input of len {len(user)}"


def make_backend(kind: str, model: str | None = None) -> Backend:
    if kind == "mock":
        return MockBackend()
    if kind == "claude":
        return ClaudeCLIBackend(model=model)
    raise ValueError(f"unknown backend {kind!r} (use 'claude' or 'mock')")

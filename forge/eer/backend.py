"""LLM backends. Real runs go through the `claude` CLI (no API key setup needed,
which is the point for a first-time builder). The mock backend is deterministic so
tests and dry-runs work fully offline."""
from __future__ import annotations
import hashlib
import shutil
import subprocess


def _smart_decode(raw: bytes | None) -> str:
    """Decode subprocess output robustly across platforms: UTF-8 first (Linux/macOS),
    cp1252 fallback (Windows console) so em-dashes/smart quotes survive rather than
    crashing or becoming replacement characters."""
    if not raw:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


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
        # Capture bytes and decode ourselves: the default locale codec (cp1252 on
        # Windows) crashes on non-ASCII model output (em-dashes, smart quotes) and
        # silently yields empty stdout. _smart_decode tries UTF-8 (Linux/macOS) then
        # cp1252 (Windows), so em-dashes survive instead of becoming replacement chars.
        proc = subprocess.run(cmd, capture_output=True, timeout=self.timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"claude CLI failed ({proc.returncode}): {_smart_decode(proc.stderr).strip()}")
        return _smart_decode(proc.stdout).strip()


class AnthropicAPIBackend(Backend):
    """Direct Anthropic API via the official SDK. One persistent client for the whole
    run — no per-block process boot, so a 16-block personality finishes in ~15-25s
    instead of the ~4 min the `claude` CLI takes (one cold CLI launch per block).
    Needs `pip install anthropic` and ANTHROPIC_API_KEY in the environment."""
    name = "anthropic-api"

    def __init__(self, model: str | None = None, max_tokens: int = 1024) -> None:
        try:
            import anthropic
        except ImportError as e:  # keep the engine importable without the SDK installed
            raise RuntimeError("the api backend needs `pip install anthropic`") from e
        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the env
        self.model = model or "claude-opus-4-8"
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()


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
    if kind == "api":
        return AnthropicAPIBackend(model=model)
    raise ValueError(f"unknown backend {kind!r} (use 'claude', 'api', or 'mock')")

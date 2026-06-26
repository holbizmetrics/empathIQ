"""Optional text-to-speech for a reply. One shared helper so `run`, `chat`, and
show_results all speak the same way.

Graceful ladder, never required:
  pc-native-voice-models (Kokoro) if cloned AND its model loads  ->  Windows SAPI  ->  a note.

Every utterance runs as a tracked subprocess so stop_speaking() can kill it
mid-sentence on Ctrl-C (otherwise the detached SAPI child keeps talking after
Python exits, and the next command's voice overlaps it).
"""
from __future__ import annotations
import os
import queue
import subprocess
import sys
import tempfile
import threading

# forge/eer/voice.py -> forge/eer -> forge -> <empathIQ root>
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_proc_lock = threading.Lock()
_proc: subprocess.Popen | None = None  # the single in-flight speech process


def _run_killable(cmd: list[str], input_bytes: bytes | None = None, timeout: int | None = None) -> int:
    """Run a speech subprocess so stop_speaking() can terminate it mid-utterance."""
    global _proc
    with _proc_lock:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE if input_bytes is not None else None)
        _proc = p
    try:
        p.communicate(input=input_bytes, timeout=timeout)
        return p.returncode or 0
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        return 1
    finally:
        with _proc_lock:
            if _proc is p:
                _proc = None


def stop_speaking() -> None:
    """Kill any in-flight speech immediately (Ctrl-C / abort)."""
    with _proc_lock:
        if _proc is not None:
            try:
                _proc.terminate()
            except Exception:
                pass


def _sapi_speak(text: str) -> bool:
    """Windows SAPI — no install needed. Prefers an installed English voice. True if it spoke."""
    if os.name != "nt" or not text:
        return False
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
            tmp = f.name
        ps = ("Add-Type -AssemblyName System.Speech; "
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$en = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'en*' } "
              "| Select-Object -First 1; "
              "if ($en) { $s.SelectVoice($en.VoiceInfo.Name) }; "
              f"$t=[IO.File]::ReadAllText('{tmp}',[Text.Encoding]::UTF8); "
              "$s.Speak($t)")
        return _run_killable(["powershell", "-NoProfile", "-Command", ps], timeout=300) == 0
    except Exception:
        return False
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _kokoro_ready() -> tuple[str, bool]:
    """Return (speak.py path, whether its model files are actually present).
    speak.py exits 0 even when the model is missing, so we check the files
    ourselves — otherwise the ladder thinks it spoke and never reaches SAPI."""
    vm = os.path.join(os.path.dirname(_ROOT), "pc-native-voice-models")
    speak_py = os.path.join(vm, "speak.py")
    models = all(os.path.exists(os.path.join(vm, "models", m))
                 for m in ("kokoro-v1.0.onnx", "voices-v1.0.bin"))
    return speak_py, (os.path.exists(speak_py) and models)


def speak(text: str) -> None:
    """Speak a reply aloud via the fallback ladder. Prints a note if nothing is available."""
    if not text:
        return
    speak_py, ready = _kokoro_ready()
    if ready:
        try:
            if _run_killable([sys.executable, speak_py, "--strip-markdown"],
                             input_bytes=text.encode("utf-8"), timeout=600) == 0:
                return
        except Exception:
            pass
        print("  (Kokoro voice failed — falling back to the system voice)")
    if _sapi_speak(text):
        return
    if os.path.exists(speak_py):
        print("  (no audio: the Kokoro model files aren't downloaded — see\n"
              "   pc-native-voice-models/README — and the system voice didn't run here)")
    else:
        print("  (no text-to-speech available on this machine)")


class BackgroundSpeaker:
    """Speaks queued texts one at a time on a worker thread, so the caller never
    blocks and queued lines never talk over each other — the spoken block plays
    while the next block is still being computed. say() to enqueue; close() to
    finish the backlog; abort() to drop it and kill the current utterance."""

    def __init__(self) -> None:
        self._q: queue.Queue = queue.Queue()
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            item = self._q.get()
            if item is None:
                break
            try:
                speak(item)
            except Exception:
                pass

    def say(self, text: str) -> None:
        if text and not self._stop.is_set():
            self._q.put(text)

    def close(self) -> None:
        self._q.put(None)
        self._t.join()

    def abort(self) -> None:
        """Stop now: drop the backlog and kill the current utterance."""
        self._stop.set()
        try:
            while True:
                self._q.get_nowait()
        except queue.Empty:
            pass
        stop_speaking()
        self._q.put(None)
        self._t.join(timeout=3)

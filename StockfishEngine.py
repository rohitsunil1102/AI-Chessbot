"""Small UCI adapter for a locally installed Stockfish executable."""

import os
import queue
import shutil
import subprocess
import threading
from pathlib import Path


class StockfishEngine:
    def __init__(self):
        configured = os.environ.get("STOCKFISH_EXECUTABLE")
        local_app_data = os.environ.get("LOCALAPPDATA")
        installed_copy = (
            Path(local_app_data) / "Programs" / "Stockfish" / "stockfish" /
            "stockfish-windows-x86-64-universal.exe"
            if local_app_data else None
        )
        executable = configured or shutil.which("stockfish") or shutil.which("stockfish.exe")
        if not executable and installed_copy and installed_copy.is_file():
            executable = str(installed_copy)
        if not executable:
            raise FileNotFoundError(
                "Stockfish was not found. Install Stockfish and add it to PATH, "
                "or set STOCKFISH_EXECUTABLE to the engine executable."
            )

        self.process = subprocess.Popen(
            [executable], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self.score_cp = None
        self.score_mate = None
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read_output, daemon=True)
        self.reader.start()
        self._send("uci")
        self._wait_for("uciok", 10)
        self._send("isready")
        self._wait_for("readyok", 10)

    def _read_output(self):
        for line in self.process.stdout:
            self.lines.put(line.strip())

    def _send(self, command):
        if self.process.poll() is not None:
            raise RuntimeError("Stockfish stopped unexpectedly.")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def _wait_for(self, expected, timeout):
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty as exc:
                raise RuntimeError("Stockfish did not respond in time.") from exc
            if line == expected:
                return
            if self.process.poll() is not None:
                raise RuntimeError("Stockfish stopped unexpectedly.")

    def best_move(self, moves, move_time_ms=700):
        self.score_cp = None
        self.score_mate = None
        command = "position startpos"
        if moves:
            command += " moves " + " ".join(moves)
        self._send(command)
        self._send(f"go movetime {move_time_ms}")
        while True:
            try:
                line = self.lines.get(timeout=max(10, move_time_ms / 1000 + 5))
            except queue.Empty as exc:
                raise RuntimeError("Stockfish did not finish its search in time.") from exc
            self._capture_score(line)
            if line.startswith("bestmove "):
                move = line.split()[1]
                return None if move == "(none)" else move

    def _capture_score(self, line):
        tokens = line.split()
        try:
            score_index = tokens.index("score")
            score_type = tokens[score_index + 1]
            value = int(tokens[score_index + 2])
        except (ValueError, IndexError):
            return
        if score_type == "cp":
            self.score_cp = value
            self.score_mate = None
        elif score_type == "mate":
            self.score_mate = value
            self.score_cp = None

    def score_white_pawns(self, white_to_move):
        """Return the latest UCI score from White's perspective, in pawn units."""
        if self.score_mate is not None:
            score = 10.0 if self.score_mate > 0 else -10.0 if self.score_mate < 0 else 0.0
        elif self.score_cp is not None:
            score = self.score_cp / 100.0
        else:
            return 0.0
        return score if white_to_move else -score

    def close(self):
        if self.process.poll() is None:
            try:
                self._send("quit")
                self.process.wait(timeout=2)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait()

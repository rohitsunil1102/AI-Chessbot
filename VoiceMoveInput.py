"""Background microphone capture and spoken chess-move parsing."""

import queue
import re
import os
import threading
import time


NUMBER_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
}

PIECE_WORDS = {
    "pawn": "p",
    "knight": "N",
    "night": "N",
    "horse": "N",
    "bishop": "B",
    "rook": "R",
    "queen": "Q",
    "king": "K",
}


def _normalize_speech(text):
    text = text.lower().replace("-", " ")
    for word, digit in NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", digit, text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def findSpokenMove(text, validMoves):
    """Match coordinate notation or a piece plus destination to a legal move."""
    normalized = _normalize_speech(text)
    files = "abcdefgh"

    coordinates = re.search(
        r"\b([a-h])\s*([1-8])\s*(?:to|into|onto|and)?\s*([a-h])\s*([1-8])\b",
        normalized,
    )
    candidates = []
    if coordinates:
        start_file, start_rank, end_file, end_rank = coordinates.groups()
        start = (8 - int(start_rank), files.index(start_file))
        end = (8 - int(end_rank), files.index(end_file))
        candidates = [
            move for move in validMoves
            if (move.startRow, move.startCol) == start
            and (move.endRow, move.endCol) == end
        ]
    else:
        destination = re.search(r"\b([a-h])\s*([1-8])\b", normalized)
        if not destination:
            return None

        end_file, end_rank = destination.groups()
        end = (8 - int(end_rank), files.index(end_file))
        candidates = [
            move for move in validMoves
            if (move.endRow, move.endCol) == end
        ]

        piece = next(
            (kind for name, kind in PIECE_WORDS.items()
             if re.search(rf"\b{name}\b", normalized)),
            None,
        )
        if piece:
            candidates = [
                move for move in candidates
                if move.pieceMove[1] == piece
            ]

    return candidates[0] if len(candidates) == 1 else None


class VoiceMoveListener:
    """Capture and transcribe speech off the Pygame thread while enabled."""

    def __init__(self):
        self.messages = queue.Queue()
        self._lock = threading.Lock()
        self._enabled = False
        self._generation = 0
        self._shutdown = threading.Event()
        self._wake = threading.Event()
        self._groq_client = None
        self._thread = threading.Thread(
            target=self._run, name="chess-voice-listener", daemon=True
        )
        self._thread.start()

    @property
    def generation(self):
        with self._lock:
            return self._generation

    @property
    def enabled(self):
        with self._lock:
            return self._enabled

    def set_enabled(self, enabled):
        with self._lock:
            if self._enabled != enabled:
                self._enabled = enabled
                self._generation += 1
            generation = self._generation
        if enabled:
            self._wake.set()
        else:
            self._wake.clear()
        return generation

    def close(self):
        self.set_enabled(False)
        self._shutdown.set()
        self._wake.set()

    def _current_session(self, generation):
        with self._lock:
            return self._enabled and self._generation == generation

    def _run(self):
        while not self._shutdown.is_set():
            self._wake.wait()
            self._wake.clear()
            if self._shutdown.is_set():
                break
            with self._lock:
                if not self._enabled:
                    continue
                generation = self._generation

            self._listen_session(generation)

    def _listen_session(self, generation):
        try:
            import speech_recognition as sr
            from groq import Groq

            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                self.messages.put((
                    generation,
                    "error",
                    "Set GROQ_API_KEY to enable voice moves.",
                    None,
                ))
                return

            if not self._current_session(generation):
                return
            if self._groq_client is None:
                self._groq_client = Groq(api_key=api_key)

            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.55
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                if not self._current_session(generation):
                    return
                self.messages.put((generation, "status", "Voice moves ready. Say e two to e four.", None))

                while self._current_session(generation) and not self._shutdown.is_set():
                    try:
                        audio = recognizer.listen(
                            source, timeout=0.5, phrase_time_limit=4
                        )
                    except sr.WaitTimeoutError:
                        continue

                    if not self._current_session(generation):
                        break
                    wavAudio = audio.get_wav_data(convert_rate=16000, convert_width=2)
                    self.messages.put((generation, "status", "Transcribing move...", None))
                    result = self._groq_client.audio.transcriptions.create(
                        file=("spoken_move.wav", wavAudio),
                        model="whisper-large-v3-turbo",
                        prompt=(
                            "Spoken chess move. Board files are a through h and ranks are one through eight. "
                            "Examples: e two to e four, knight f three, bishop takes c four."
                        ),
                        language="en",
                        temperature=0.0,
                    )
                    text = result.text.strip()
                    if not text:
                        self.messages.put((generation, "status", "Didn't catch that. Try saying e2 to e4.", None))
                        continue

                    if self._current_session(generation):
                        self.messages.put((generation, "speech", text, time.monotonic()))
        except ImportError:
            if self._current_session(generation):
                self.messages.put((generation, "error", "Install voice support: pip install -r requirements.txt", None))
        except (OSError, AttributeError) as exc:
            if self._current_session(generation):
                self.messages.put((generation, "error", f"Microphone unavailable: {exc}", None))
        except Exception as exc:
            if self._current_session(generation):
                # Keep the on-screen message short, but preserve the API's full
                # response in the console so permission/configuration errors can
                # be diagnosed without the Pygame status line truncating them.
                print(f"Groq transcription failed: {exc!r}")
                error_text = str(exc).lower()
                if (
                    getattr(exc, "status_code", None) == 403
                    and ("network settings" in error_text or "access denied" in error_text)
                ):
                    message = "Groq 403: network denied; try another network."
                elif getattr(exc, "status_code", None) == 403:
                    message = "Groq 403: check model access in Console settings."
                else:
                    message = f"Groq transcription failed: {exc}"
                self.messages.put((generation, "error", message, None))

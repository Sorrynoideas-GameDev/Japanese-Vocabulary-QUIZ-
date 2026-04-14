"""
data_loader.py
--------------
Handles loading and saving of vocabulary data and user progress.
Designed to be PyInstaller-compatible (uses sys._MEIPASS for bundled resources).
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource, works for both dev mode and PyInstaller bundles.
    PyInstaller extracts bundled files to sys._MEIPASS at runtime.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def user_data_path(filename: str) -> str:
    """
    Return a writable path for user-specific data (progress files).
    Uses the directory of the executable so progress persists across runs.
    """
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Word:
    """Represents a single vocabulary entry."""
    id: int
    english: str
    romaji: str
    kana: str
    session_introduced: int = -1  # -1 means not yet introduced

    def __eq__(self, other):
        return isinstance(other, Word) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class Progress:
    """Tracks the user's learning progress across sessions."""
    current_session: int = 0
    seen_word_ids: List[int] = field(default_factory=list)
    # Optional: per-word accuracy tracking {word_id: [correct_count, total_count]}
    word_accuracy: dict = field(default_factory=dict)

    def record_answer(self, word_id: int, correct: bool):
        """Update per-word accuracy stats."""
        if word_id not in self.word_accuracy:
            self.word_accuracy[word_id] = [0, 0]
        self.word_accuracy[word_id][1] += 1
        if correct:
            self.word_accuracy[word_id][0] += 1

    def get_accuracy(self, word_id: int) -> Optional[float]:
        """Return accuracy ratio for a word, or None if never seen."""
        stats = self.word_accuracy.get(word_id)
        if not stats or stats[1] == 0:
            return None
        return stats[0] / stats[1]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_vocabulary(vocab_path: str = "vocabulary.json") -> List[Word]:
    """
    Load vocabulary from a JSON file and parse into Word objects.
    Falls back to resource_path for bundled executables.
    """
    # Try direct path first (dev mode), then bundled path
    full_path = vocab_path if os.path.isabs(vocab_path) else resource_path(vocab_path)
    if not os.path.exists(full_path):
        # Last resort: same directory as script
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), vocab_path)

    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = []
    for entry in data:
        words.append(Word(
            id=entry["id"],
            english=entry["english"],
            romaji=entry["romaji"],
            kana=entry["kana"],
        ))
    return words


def load_progress(progress_path: str = "progress.json") -> Progress:
    """
    Load user progress from a JSON file.
    If the file doesn't exist, returns a fresh Progress object.
    """
    full_path = user_data_path(progress_path)
    if not os.path.exists(full_path):
        return Progress(current_session=0, seen_word_ids=[])

    with open(full_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Progress(
        current_session=data.get("current_session", 0),
        seen_word_ids=data.get("seen_word_ids", []),
        word_accuracy=data.get("word_accuracy", {}),
    )


def save_progress(progress: Progress, progress_path: str = "progress.json"):
    """Persist current progress to a JSON file."""
    full_path = user_data_path(progress_path)
    data = {
        "current_session": progress.current_session,
        "seen_word_ids": progress.seen_word_ids,
        "word_accuracy": progress.word_accuracy,
    }
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

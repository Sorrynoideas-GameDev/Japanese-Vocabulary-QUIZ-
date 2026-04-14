"""
main.py
-------
Application entry point and controller.

Orchestrates the flow between screens:
  HomeScreen → NewWordsScreen (on Next Session)
             → QuizScreen (on Start Practice)
             → ResultsScreen (on quiz complete)
             → HomeScreen (on home button)

Also manages loading/saving of vocabulary and progress data.
"""

import os
import sys
from data_loader import load_vocabulary, load_progress, save_progress
from scheduler import (
    build_quiz_pool, advance_session,
    get_seen_words, get_unseen_words, build_session_word_map,
)
from quiz_engine import QuizSession
from ui import App, HomeScreen, QuizScreen, ResultsScreen, NewWordsScreen

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return filename


class Controller:
    """
    Central controller that wires data, logic, and UI screens together.
    Each screen transition is a method on this class.
    """

    def __init__(self):
        # ── Load data ────────────────────────────────────────────────────
        self.all_words = load_vocabulary(get_resource_path("vocabulary.json"))
        self.progress = load_progress("progress.json")

        # Stamp session_introduced onto seen words from progress data
        word_map = build_session_word_map(self.all_words, self.progress)
        self.all_words = list(word_map.values())

        # ── Bootstrap: if no session started yet, prompt for first session
        # (handled gracefully in HomeScreen which disables quiz if no words)

        # ── Create root window ───────────────────────────────────────────
        self.app = App()
        self.app.protocol("WM_DELETE_WINDOW", self._on_quit)

        # Navigate to home
        self._go_home()
        self.app.mainloop()

    # ── Screen Navigation ────────────────────────────────────────────────

    def _go_home(self):
        """Show the home screen."""
        self._destroy_current()
        remaining = len(get_unseen_words(self.all_words, self.progress))
        self._current = HomeScreen(
            self.app,
            on_start_quiz=self._start_quiz,
            on_next_session=self._next_session,
            progress=self.progress,
            total_vocab=len(self.all_words),
            words_remaining=remaining,
        )
        self.app.show_frame(self._current)

    def _next_session(self):
        """Advance the session counter and introduce new words."""
        self._destroy_current()
        unseen = get_unseen_words(self.all_words, self.progress)
        if not unseen:
            # All words learned — just go home
            self._go_home()
            return

        new_words = advance_session(self.all_words, self.progress)

        self._current = NewWordsScreen(
            self.app,
            new_words=new_words,
            session_num=self.progress.current_session,
            on_continue=self._start_quiz,
        )
        self.app.show_frame(self._current)

    def _start_quiz(self):
        """Build the quiz pool and show the quiz screen."""
        self._destroy_current()

        seen = get_seen_words(self.all_words, self.progress)
        pool = build_quiz_pool(self.all_words, self.progress)

        if not pool:
            # Edge case: no words introduced yet
            self._go_home()
            return

        session = QuizSession(pool, seen, self.progress)

        self._current = QuizScreen(
            self.app,
            session=session,
            on_complete=self._show_results,
        )
        self.app.show_frame(self._current)

    def _show_results(self, results: dict):
        """Show the results screen after quiz completion."""
        # Save progress (per-word accuracy was updated during quiz)
        save_progress(self.progress)

        self._destroy_current()
        remaining = len(get_unseen_words(self.all_words, self.progress))

        self._current = ResultsScreen(
            self.app,
            results=results,
            on_home=self._go_home,
            on_next_session=self._next_session,
            words_remaining=remaining,
        )
        self.app.show_frame(self._current)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _destroy_current(self):
        """Destroy and remove the currently displayed screen frame."""
        if hasattr(self, "_current") and self._current:
            self._current.destroy()
            self._current = None

    def _on_quit(self):
        """Save progress and exit cleanly."""
        save_progress(self.progress)
        self.app.destroy()
        sys.exit(0)


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    Controller()

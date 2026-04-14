"""
ui.py
-----
Tkinter-based UI for the Japanese Vocabulary Learning application.

Design aesthetic: Refined dark theme with ink-brush-inspired accents.
Palette drawn from traditional Japanese design: deep indigo, warm ivory,
vermillion accents, with generous spacing and clean typography.

Keyboard shortcuts:
  1 / 2 / 3  → Select option 1 / 2 / 3
  Enter / Space → Next question (after answering)
  N → Advance to next session (on home screen)
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, List, Optional

from data_loader import Word, Progress
from quiz_engine import Question, QuizSession


# ---------------------------------------------------------------------------
# Colour & Style Constants
# ---------------------------------------------------------------------------

BG_DARK       = "#0f0f14"      # Deep void background
BG_CARD       = "#1a1a24"      # Slightly lighter card surface
BG_HOVER      = "#22223a"      # Subtle hover state for cards
ACCENT_RED    = "#c0392b"      # Vermillion / Japanese red
ACCENT_GOLD   = "#d4af37"      # Warm gold for highlights
TEXT_PRIMARY  = "#f0ece0"      # Warm ivory for primary text
TEXT_MUTED    = "#7a7a9a"      # Muted secondary text
TEXT_KANA     = "#e8e0d0"      # Slightly warm for kana characters
SUCCESS       = "#27ae60"      # Correct answer green
ERROR         = "#c0392b"      # Wrong answer red
OPTION_BORDER = "#2e2e48"      # Default button border
BTN_FG        = "#f0ece0"      # Button text color

FONT_TITLE    = ("Georgia", 28, "bold")
FONT_SUBTITLE = ("Georgia", 14, "italic")
FONT_ENGLISH  = ("Georgia", 32, "bold")
FONT_KANA     = ("", 26, "bold")          # Default system font for kana
FONT_BODY     = ("Georgia", 13)
FONT_SMALL    = ("Georgia", 11)
FONT_COUNTER  = ("Courier", 11)
FONT_SESSION  = ("Georgia", 18, "bold")
FONT_RESULT_BIG = ("Georgia", 48, "bold")


def _make_canvas_button(
    parent,
    text: str,
    command: Callable,
    width: int = 380,
    height: int = 70,
    bg: str = BG_CARD,
    fg: str = TEXT_KANA,
    font=None,
    border_color: str = OPTION_BORDER,
    tag: str = "",
) -> tk.Canvas:
    """
    Create a rounded-rectangle canvas button.
    Returns the canvas widget; caller must grid/pack it.
    """
    if font is None:
        font = FONT_KANA

    cv = tk.Canvas(
        parent,
        width=width, height=height,
        bg=BG_DARK, highlightthickness=0,
        cursor="hand2",
    )

    r = 12  # corner radius
    # Draw rounded rect
    rect_id = _rounded_rect(cv, 4, 4, width - 4, height - 4, r, fill=bg, outline=border_color, width=2)
    text_id = cv.create_text(
        width // 2, height // 2,
        text=text, fill=fg, font=font,
        anchor="center",
    )

    def on_enter(e):
        cv.itemconfig(rect_id, fill=BG_HOVER, outline=ACCENT_GOLD)

    def on_leave(e):
        cv.itemconfig(rect_id, fill=bg, outline=border_color)

    def on_click(e):
        command()

    cv.bind("<Enter>", on_enter)
    cv.bind("<Leave>", on_leave)
    cv.bind("<Button-1>", on_click)
    cv.tag_bind(rect_id, "<Enter>", on_enter)
    cv.tag_bind(rect_id, "<Leave>", on_leave)
    cv.tag_bind(rect_id, "<Button-1>", on_click)
    cv.tag_bind(text_id, "<Enter>", on_enter)
    cv.tag_bind(text_id, "<Leave>", on_leave)
    cv.tag_bind(text_id, "<Button-1>", on_click)

    cv._rect_id = rect_id
    cv._text_id = text_id
    cv._default_bg = bg
    cv._default_border = border_color
    return cv


def _rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a rounded rectangle on a canvas and return its item id."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class App(tk.Tk):
    """Root application window. Manages all screens via frame switching."""

    def __init__(self):
        super().__init__()
        self.title("日本語 — Japanese Vocabulary")
        self.configure(bg=BG_DARK)
        
        # Start maximized
        self.state("zoomed")   # Windows

        # Allow resizing
        self.resizable(True, True)

        # Optional: set minimum size so UI doesn't break
        self.minsize(600, 500)

        # Container holds all screens; they stack on top of each other
        self._container = tk.Frame(self, bg=BG_DARK)
        self._container.pack(fill="both", expand=True)
        self._container.grid_rowconfigure(0, weight=1)
        self._container.grid_columnconfigure(0, weight=1)

        self._frames: dict = {}
        self._current_frame = None

    def _center_window(self, w: int, h: int):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def show_frame(self, frame: tk.Frame):
        """Raise a frame to the top."""
        if self._current_frame:
            self._current_frame.pack_forget()
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        frame.tkraise()


# ---------------------------------------------------------------------------
# Home Screen
# ---------------------------------------------------------------------------

class HomeScreen(tk.Frame):
    """
    Landing screen showing session info and action buttons.
    
    Buttons:
      - Start Practice  → runs the quiz for current session's word pool
      - Next Session    → introduces 10 new words, increments session
    """

    def __init__(self, parent: App, on_start_quiz: Callable, on_next_session: Callable,
                 progress: Progress, total_vocab: int, words_remaining: int):
        super().__init__(parent, bg=BG_DARK)
        self._on_start_quiz = on_start_quiz
        self._on_next_session = on_next_session

        self._build_ui(progress, total_vocab, words_remaining)

        # Keyboard shortcut: N for next session
        parent.bind_all("<n>", lambda e: on_next_session())
        parent.bind_all("<N>", lambda e: on_next_session())

    def _build_ui(self, progress: Progress, total_vocab: int, words_remaining: int):
        # ── Top accent bar ──────────────────────────────────────────────
        tk.Frame(self, bg=ACCENT_RED, height=4).pack(fill="x")

        # ── Title ───────────────────────────────────────────────────────
        tk.Label(
            self, text="日本語", font=("", 52, "bold"),
            bg=BG_DARK, fg=TEXT_PRIMARY,
        ).pack(pady=(40, 0))

        tk.Label(
            self, text="Vocabulary Trainer",
            font=FONT_SUBTITLE, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(0, 40))

        # ── Session info card ────────────────────────────────────────────
        card = tk.Frame(self, bg=BG_CARD, padx=30, pady=24)
        card.pack(padx=50, fill="x")

        info_rows = [
            ("Session",           str(progress.current_session) if progress.current_session > 0 else "—"),
            ("Words Learned",     str(len(progress.seen_word_ids))),
            ("Words Remaining",   str(words_remaining)),
            ("Total Vocabulary",  str(total_vocab)),
        ]

        for label, value in info_rows:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=FONT_BODY, bg=BG_CARD, fg=TEXT_MUTED, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=FONT_BODY, bg=BG_CARD, fg=TEXT_PRIMARY, anchor="e").pack(side="right")

        # Divider
        tk.Frame(card, bg=OPTION_BORDER, height=1).pack(fill="x", pady=(12, 0))

        # Seen word accuracy summary
        total_attempts = sum(v[1] for v in progress.word_accuracy.values())
        total_correct = sum(v[0] for v in progress.word_accuracy.values())
        if total_attempts > 0:
            overall_acc = total_correct / total_attempts * 100
            acc_text = f"{overall_acc:.1f}%  overall accuracy"
        else:
            acc_text = "No quiz history yet"

        tk.Label(
            card, text=acc_text,
            font=FONT_SMALL, bg=BG_CARD, fg=ACCENT_GOLD,
        ).pack(pady=(10, 0))

        # ── Buttons ──────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(pady=32)

        # Start Practice (only if there are seen words)
        can_quiz = len(progress.seen_word_ids) > 0
        start_label = "Start Practice" if can_quiz else "No words yet — start a session first"

        start_btn = _make_canvas_button(
            btn_frame,
            text=start_label,
            command=self._on_start_quiz if can_quiz else lambda: None,
            width=380, height=62,
            bg=ACCENT_RED if can_quiz else BG_CARD,
            fg=TEXT_PRIMARY,
            font=("Georgia", 15, "bold"),
            border_color=ACCENT_RED if can_quiz else OPTION_BORDER,
        )
        start_btn.pack(pady=8)

        # Next Session
        can_advance = words_remaining > 0
        next_label = "Next Session  [N]" if can_advance else "All words introduced!"
        next_btn = _make_canvas_button(
            btn_frame,
            text=next_label,
            command=self._on_next_session if can_advance else lambda: None,
            width=380, height=62,
            bg=BG_CARD,
            fg=TEXT_PRIMARY if can_advance else TEXT_MUTED,
            font=("Georgia", 15),
            border_color=ACCENT_GOLD if can_advance else OPTION_BORDER,
        )
        next_btn.pack(pady=8)

        # Footer hint
        tk.Label(
            self,
            text="Keyboard: 1 / 2 / 3 to answer  •  N for next session",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(side="bottom", pady=16)


# ---------------------------------------------------------------------------
# Quiz Screen
# ---------------------------------------------------------------------------

class QuizScreen(tk.Frame):
    """
    Main quiz interface.

    Displays:
      - Progress counter (e.g. 3 / 45)
      - English prompt
      - Three kana option buttons
      - Feedback after answering
      - Auto-advances after brief delay, or waits for Enter/Space/Next btn
    """

    FEEDBACK_DELAY_MS = 900  # ms to pause after showing correct/wrong feedback

    def __init__(self, parent: App, session: QuizSession, on_complete: Callable):
        super().__init__(parent, bg=BG_DARK)
        self._parent = parent
        self._session = session
        self._on_complete = on_complete
        self._answered = False
        self._option_canvases: List[tk.Canvas] = []
        self._advance_job = None  # pending after() job id

        self._build_static_ui()
        self._bind_keys()

        # Start the first question
        self._show_next_question()

    # ── Layout Construction ─────────────────────────────────────────────

    def _build_static_ui(self):
        tk.Frame(self, bg=ACCENT_RED, height=4).pack(fill="x")

        # ── Top bar: session label + progress ───────────────────────────
        top = tk.Frame(self, bg=BG_DARK)
        top.pack(fill="x", padx=24, pady=(16, 0))

        tk.Label(top, text="Practice", font=FONT_BODY, bg=BG_DARK, fg=TEXT_MUTED).pack(side="left")
        self._progress_label = tk.Label(
            top, text="", font=FONT_COUNTER, bg=BG_DARK, fg=TEXT_MUTED,
        )
        self._progress_label.pack(side="right")

        # Progress bar (canvas)
        self._progress_cv = tk.Canvas(self, height=3, bg=BG_CARD, highlightthickness=0)
        self._progress_cv.pack(fill="x", padx=0)
        self._progress_bar = self._progress_cv.create_rectangle(0, 0, 0, 3, fill=ACCENT_RED, outline="")

        # ── English prompt area ─────────────────────────────────────────
        prompt_frame = tk.Frame(self, bg=BG_DARK)
        prompt_frame.pack(pady=(50, 10), padx=30)

        tk.Label(
            prompt_frame, text="What is the kana for:",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack()

        self._english_label = tk.Label(
            prompt_frame, text="",
            font=FONT_ENGLISH, bg=BG_DARK, fg=TEXT_PRIMARY,
            wraplength=440,
        )
        self._english_label.pack(pady=(6, 0))

        # ── Feedback label ──────────────────────────────────────────────
        self._feedback_label = tk.Label(
            self, text="", font=("Georgia", 13, "italic"),
            bg=BG_DARK, fg=SUCCESS,
        )
        self._feedback_label.pack(pady=(4, 0))

        # ── Option buttons ──────────────────────────────────────────────
        self._options_frame = tk.Frame(self, bg=BG_DARK)
        self._options_frame.pack(pady=24)

        for i in range(3):
            cv = _make_canvas_button(
                self._options_frame,
                text="",
                command=lambda idx=i: self._on_option_click(idx),
                width=420, height=72,
            )
            cv.pack(pady=7)
            self._option_canvases.append(cv)

        # ── Score strip ─────────────────────────────────────────────────
        score_strip = tk.Frame(self, bg=BG_CARD)
        score_strip.pack(fill="x", side="bottom")

        self._score_label = tk.Label(
            score_strip, text="", font=FONT_BODY,
            bg=BG_CARD, fg=TEXT_MUTED, pady=10,
        )
        self._score_label.pack()

    # ── Question Display ────────────────────────────────────────────────

    def _show_next_question(self):
        """Advance to the next question or complete the session."""
        self._cancel_advance_job()

        q = self._session.next_question()
        if q is None:
            self._on_complete(self._session.get_results())
            return

        self._answered = False
        self._current_question = q

        # Update progress counter and bar
        done = self._session.current_index
        total = self._session.total
        pct = done / total if total > 0 else 0
        self._progress_label.config(text=f"{done} / {total}")

        # Draw progress bar proportional to canvas width
        bar_w = self._progress_cv.winfo_width()
        self._progress_cv.coords(self._progress_bar, 0, 0, bar_w * pct, 3)

        # Update English prompt
        self._english_label.config(text=q.prompt.upper())

        # Clear feedback
        self._feedback_label.config(text="")

        # Update option buttons
        for i, cv in enumerate(self._option_canvases):
            word = q.options[i]
            # Reset style
            cv.itemconfig(cv._rect_id, fill=BG_CARD, outline=OPTION_BORDER)
            cv.itemconfig(cv._text_id, text=word.kana, fill=TEXT_KANA)

        # Update score strip
        c = self._session.correct_count
        t = self._session.current_index - 1
        acc = f"{c/t*100:.0f}%" if t > 0 else "—"
        self._score_label.config(text=f"Correct: {c}  ·  Accuracy: {acc}")

    # ── Answer Handling ─────────────────────────────────────────────────

    def _on_option_click(self, idx: int):
        if self._answered:
            return
        self._answered = True

        q = self._current_question
        chosen_word = q.options[idx]
        is_correct = self._session.submit_answer(chosen_word)

        # Highlight chosen and correct buttons
        for i, cv in enumerate(self._option_canvases):
            word = q.options[i]
            if word.id == q.correct_word.id:
                # Always highlight correct answer in green
                cv.itemconfig(cv._rect_id, fill="#1a3d2b", outline=SUCCESS)
                cv.itemconfig(cv._text_id, fill=SUCCESS)
            elif i == idx and not is_correct:
                # Highlight wrong choice in red
                cv.itemconfig(cv._rect_id, fill="#3d1a1a", outline=ERROR)
                cv.itemconfig(cv._text_id, fill=ERROR)

        # Feedback text
        if is_correct:
            self._feedback_label.config(
                text="✓  Correct!", fg=SUCCESS,
            )
        else:
            self._feedback_label.config(
                text=f"✗  The answer was  {q.correct_word.kana}  ({q.correct_word.romaji})",
                fg=ERROR,
            )

        # Auto-advance after delay
        self._advance_job = self.after(self.FEEDBACK_DELAY_MS, self._show_next_question)

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self._parent.bind_all("1", lambda e: self._on_option_click(0))
        self._parent.bind_all("2", lambda e: self._on_option_click(1))
        self._parent.bind_all("3", lambda e: self._on_option_click(2))
        self._parent.bind_all("<Return>", lambda e: self._show_next_question() if self._answered else None)
        self._parent.bind_all("<space>", lambda e: self._show_next_question() if self._answered else None)

    def _cancel_advance_job(self):
        if self._advance_job is not None:
            self.after_cancel(self._advance_job)
            self._advance_job = None

    def destroy(self):
        """Unbind keys when screen is destroyed."""
        self._cancel_advance_job()
        for key in ("1", "2", "3", "<Return>", "<space>"):
            try:
                self._parent.unbind_all(key)
            except Exception:
                pass
        super().destroy()


# ---------------------------------------------------------------------------
# Results Screen
# ---------------------------------------------------------------------------

class ResultsScreen(tk.Frame):
    """
    Shown after completing the quiz pool.
    Displays total / correct / accuracy with a visual ring.
    """

    def __init__(self, parent: App, results: dict,
                 on_home: Callable, on_next_session: Callable,
                 words_remaining: int):
        super().__init__(parent, bg=BG_DARK)
        self._build_ui(results, on_home, on_next_session, words_remaining)

    def _build_ui(self, results: dict, on_home: Callable,
                  on_next_session: Callable, words_remaining: int):
        tk.Frame(self, bg=ACCENT_GOLD, height=4).pack(fill="x")

        tk.Label(
            self, text="Session Complete",
            font=FONT_SESSION, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(40, 0))

        # ── Accuracy ring (canvas) ───────────────────────────────────────
        cv = tk.Canvas(self, width=200, height=200, bg=BG_DARK, highlightthickness=0)
        cv.pack(pady=20)

        accuracy = results["accuracy"]
        extent = accuracy / 100 * 359.9  # degrees; 360 causes arc to disappear

        # Background ring
        cv.create_arc(20, 20, 180, 180, start=90, extent=359.9,
                      style="arc", outline=BG_CARD, width=18)
        # Foreground arc
        color = SUCCESS if accuracy >= 70 else (ACCENT_GOLD if accuracy >= 50 else ERROR)
        cv.create_arc(20, 20, 180, 180, start=90, extent=-extent,
                      style="arc", outline=color, width=18)
        # Centre text
        cv.create_text(100, 90, text=f"{accuracy:.0f}%",
                        font=FONT_RESULT_BIG, fill=TEXT_PRIMARY)
        cv.create_text(100, 140, text="accuracy",
                        font=FONT_SMALL, fill=TEXT_MUTED)

        # ── Stats row ────────────────────────────────────────────────────
        stats_frame = tk.Frame(self, bg=BG_CARD)
        stats_frame.pack(padx=60, fill="x")

        for label, val in [
            ("Total Questions",   str(results["total"])),
            ("Correct",           str(results["correct"])),
            ("Incorrect",         str(results["incorrect"])),
        ]:
            row = tk.Frame(stats_frame, bg=BG_CARD)
            row.pack(fill="x", pady=5, padx=20)
            tk.Label(row, text=label, font=FONT_BODY, bg=BG_CARD, fg=TEXT_MUTED, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_BODY, bg=BG_CARD, fg=TEXT_PRIMARY, anchor="e").pack(side="right")

        # ── Buttons ──────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(pady=28)

        _make_canvas_button(
            btn_frame, text="Practice Again",
            command=on_home,
            width=360, height=60,
            bg=ACCENT_RED, fg=TEXT_PRIMARY,
            font=("Georgia", 14, "bold"),
            border_color=ACCENT_RED,
        ).pack(pady=7)

        if words_remaining > 0:
            _make_canvas_button(
                btn_frame, text="Next Session  [N]",
                command=on_next_session,
                width=360, height=60,
                bg=BG_CARD, fg=TEXT_PRIMARY,
                font=("Georgia", 14),
                border_color=ACCENT_GOLD,
            ).pack(pady=7)


# ---------------------------------------------------------------------------
# New Words Preview Screen
# ---------------------------------------------------------------------------

class NewWordsScreen(tk.Frame):
    """
    Shown when a new session starts, previewing the 10 new words introduced.
    """

    def __init__(self, parent: App, new_words: List[Word], session_num: int, on_continue: Callable):
        super().__init__(parent, bg=BG_DARK)
        self._build_ui(new_words, session_num, on_continue)

    def _build_ui(self, new_words: List[Word], session_num: int, on_continue: Callable):
        tk.Frame(self, bg=ACCENT_GOLD, height=4).pack(fill="x")

        tk.Label(
            self, text=f"Session {session_num}",
            font=FONT_SESSION, bg=BG_DARK, fg=ACCENT_GOLD,
        ).pack(pady=(28, 2))

        tk.Label(
            self, text="New words introduced:",
            font=FONT_BODY, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=(0, 16))

        # Scrollable list of new words
        list_frame = tk.Frame(self, bg=BG_CARD, padx=20, pady=16)
        list_frame.pack(padx=40, fill="x")

        for word in new_words:
            row = tk.Frame(list_frame, bg=BG_CARD)
            row.pack(fill="x", pady=4)

            # Kana (large)
            tk.Label(
                row, text=word.kana,
                font=("", 20, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY, anchor="w", width=6,
            ).pack(side="left")

            # Romaji
            tk.Label(
                row, text=word.romaji,
                font=("Courier", 11), bg=BG_CARD, fg=TEXT_MUTED, anchor="w", width=14,
            ).pack(side="left")

            # English
            tk.Label(
                row, text=word.english,
                font=FONT_BODY, bg=BG_CARD, fg=TEXT_MUTED, anchor="e",
            ).pack(side="right")

        tk.Label(
            self,
            text="Study these, then practice to reinforce them!",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_MUTED,
        ).pack(pady=16)

        _make_canvas_button(
            self, text="Start Practice",
            command=on_continue,
            width=360, height=62,
            bg=ACCENT_RED, fg=TEXT_PRIMARY,
            font=("Georgia", 15, "bold"),
            border_color=ACCENT_RED,
        ).pack(pady=8)

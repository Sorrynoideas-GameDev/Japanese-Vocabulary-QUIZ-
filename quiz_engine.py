"""
quiz_engine.py
--------------
Generates quiz questions with multiple-choice options.

Each question shows:
  - The English meaning as the prompt
  - Three kana options (1 correct + 2 distractors from seen words)

Distractors are drawn randomly from seen words, ensuring:
  - No duplicate options
  - The correct answer is always present
  - Edge cases with small word pools are handled gracefully
"""

import random
from dataclasses import dataclass
from typing import List, Optional

from data_loader import Word, Progress
from scheduler import get_seen_words, build_session_word_map


@dataclass
class Question:
    """Represents a single quiz question."""
    prompt: str          # English word shown to the user
    options: List[Word]  # Three Word objects (kana used for display)
    correct_word: Word   # The correct answer
    correct_index: int   # Index of correct answer in options list


def generate_options(
    correct_word: Word,
    seen_words: List[Word],
    num_options: int = 3,
) -> List[Word]:
    """
    Build a list of `num_options` Words for a multiple-choice question.
    Guarantees the correct word is included; remaining slots filled with
    unique distractors from the seen word pool.
    """
    # Pool of possible distractors (exclude the correct word)
    distractor_pool = [w for w in seen_words if w.id != correct_word.id]

    # How many distractors we can actually provide
    num_distractors = min(num_options - 1, len(distractor_pool))

    # Sample distractors without replacement to avoid duplicates
    distractors = random.sample(distractor_pool, num_distractors)

    options = [correct_word] + distractors

    # If we couldn't fill all slots (tiny word pool), pad with a placeholder
    # This is a rare edge case only in the very first session
    while len(options) < num_options:
        options.append(correct_word)  # fallback: repeat correct (still answerable)

    random.shuffle(options)
    return options


def create_question(word: Word, seen_words: List[Word]) -> Question:
    """
    Create a Question for a given word.

    Args:
        word: The vocabulary word being tested.
        seen_words: All words the user has seen (for distractor selection).

    Returns:
        A fully-formed Question object ready for display.
    """
    options = generate_options(word, seen_words, num_options=3)

    # Determine where the correct answer landed after shuffling
    correct_index = next(
        i for i, opt in enumerate(options) if opt.id == word.id
    )

    return Question(
        prompt=word.english,
        options=options,
        correct_word=word,
        correct_index=correct_index,
    )


class QuizSession:
    """
    Manages a single quiz run-through of the quiz pool.

    Tracks score, advances through questions, and provides result summaries.
    Also records per-word accuracy in the Progress object.
    """

    def __init__(self, quiz_pool: List[Word], seen_words: List[Word], progress: Progress):
        self.quiz_pool = quiz_pool          # Words to quiz (may contain repeats)
        self.seen_words = seen_words        # All seen words for distractor pool
        self.progress = progress            # Progress object for accuracy tracking
        self.total = len(quiz_pool)
        self.current_index = 0
        self.correct_count = 0
        self.current_question: Optional[Question] = None

    @property
    def is_complete(self) -> bool:
        return self.current_index >= self.total

    @property
    def questions_remaining(self) -> int:
        return self.total - self.current_index

    def next_question(self) -> Optional[Question]:
        """Advance to the next question and return it, or None if done."""
        if self.is_complete:
            return None
        word = self.quiz_pool[self.current_index]
        self.current_question = create_question(word, self.seen_words)
        self.current_index += 1
        return self.current_question

    def submit_answer(self, chosen_word: Word) -> bool:
        """
        Submit an answer for the current question.

        Returns True if correct, False otherwise.
        Also updates per-word accuracy in progress.
        """
        if self.current_question is None:
            return False

        correct = chosen_word.id == self.current_question.correct_word.id
        if correct:
            self.correct_count += 1

        # Record per-word accuracy
        self.progress.record_answer(self.current_question.correct_word.id, correct)
        return correct

    def get_results(self) -> dict:
        """Return a summary dict of the session results."""
        accuracy = (self.correct_count / self.total * 100) if self.total > 0 else 0
        return {
            "total": self.total,
            "correct": self.correct_count,
            "incorrect": self.total - self.correct_count,
            "accuracy": accuracy,
        }

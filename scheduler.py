"""
scheduler.py
------------
Implements the spaced repetition algorithm and session advancement logic.

Repetition rules based on word age (current_session - session_introduced):
    age == 0     → 5 repetitions  (brand new word, heavily reinforced)
    age 1–5      → 4 repetitions  (recently learned)
    age 6–15     → 2 repetitions  (short-term retention check)
    age > 15     → 1 repetition   (long-term retention check)
"""

import random
from typing import List, Dict

from data_loader import Word, Progress, save_progress


WORDS_PER_SESSION = 10  # Number of new words introduced each session


def get_repetition_count(age: int) -> int:
    """
    Return how many times a word should appear in the quiz pool
    based on its age (sessions since it was introduced).
    """
    if age == 0:
        return 5
    elif 1 <= age <= 5:
        return 4
    elif 6 <= age <= 15:
        return 2
    else:
        return 1


def get_seen_words(all_words: List[Word], progress: Progress) -> List[Word]:
    """Return only the words the user has already been introduced to."""
    seen_ids = set(progress.seen_word_ids)
    return [w for w in all_words if w.id in seen_ids]


def get_unseen_words(all_words: List[Word], progress: Progress) -> List[Word]:
    """Return words not yet introduced to the user."""
    seen_ids = set(progress.seen_word_ids)
    return [w for w in all_words if w.id not in seen_ids]


def build_session_word_map(all_words: List[Word], progress: Progress) -> Dict[int, Word]:
    """
    Build a quick lookup: word_id → Word, but also stamps session_introduced
    from the progress data onto each seen word.

    This is needed because vocabulary.json stores words without session_introduced;
    that data lives in progress.json via the seen_word_ids order.
    """
    # Reconstruct session_introduced from the order words were added to seen_word_ids.
    # We store session assignments in progress.word_sessions dict if available,
    # otherwise fall back to approximation (first WORDS_PER_SESSION words = session 1, etc.)
    word_map = {w.id: w for w in all_words}

    # If we have explicit session data, use it
    if hasattr(progress, 'word_sessions') and progress.word_sessions:
        for wid, sess in progress.word_sessions.items():
            if int(wid) in word_map:
                word_map[int(wid)].session_introduced = sess
    else:
        # Derive from seen_word_ids ordering (10 per session starting at session 1)
        for idx, wid in enumerate(progress.seen_word_ids):
            session_num = (idx // WORDS_PER_SESSION) + 1
            if wid in word_map:
                word_map[wid].session_introduced = session_num

    return word_map


def build_quiz_pool(all_words: List[Word], progress: Progress) -> List[Word]:
    """
    Build the ordered quiz pool for the current session.

    Each seen word appears in the pool according to its repetition count
    (determined by how old it is relative to the current session).
    The pool is shuffled for random presentation order.
    """
    word_map = build_session_word_map(all_words, progress)
    seen_ids = set(progress.seen_word_ids)
    current_session = progress.current_session

    quiz_pool: List[Word] = []

    for wid in progress.seen_word_ids:
        word = word_map.get(wid)
        if word is None:
            continue
        if word.session_introduced < 0:
            continue  # Not properly introduced yet

        age = current_session - word.session_introduced
        reps = get_repetition_count(age)

        # Add the word `reps` times to increase quiz frequency
        quiz_pool.extend([word] * reps)

    random.shuffle(quiz_pool)
    return quiz_pool


def advance_session(all_words: List[Word], progress: Progress) -> List[Word]:
    """
    Advance to the next session:
      1. Increment session counter
      2. Select the next WORDS_PER_SESSION unseen words
      3. Mark them as introduced in this new session
      4. Save progress

    Returns the list of newly introduced words.
    """
    progress.current_session += 1
    unseen = get_unseen_words(all_words, progress)

    # Take up to WORDS_PER_SESSION new words
    new_words = unseen[:WORDS_PER_SESSION]

    # Stamp the current session onto each new word
    for word in new_words:
        word.session_introduced = progress.current_session
        progress.seen_word_ids.append(word.id)

    # Persist word→session mapping in progress for reliable reconstruction
    if not hasattr(progress, 'word_sessions'):
        progress.word_sessions = {}
    for word in new_words:
        progress.word_sessions[str(word.id)] = progress.current_session

    save_progress(progress)
    return new_words


def get_session_stats(progress: Progress) -> dict:
    """Return summary statistics for the current learning state."""
    total_seen = len(progress.seen_word_ids)
    return {
        "current_session": progress.current_session,
        "total_words_learned": total_seen,
    }

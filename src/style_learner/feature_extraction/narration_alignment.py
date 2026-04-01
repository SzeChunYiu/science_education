"""Narration alignment: maps transcript words to scene boundaries.

Aligns Whisper-generated word-level timestamps to detected scene boundaries,
groups words into sentences, computes speaking rate (WPM), and classifies
each scene's narration phase (introducing, listing, concluding, explaining).
"""

import logging
import re
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Keywords that indicate a listing narration phase
_LISTING_KEYWORDS = {
    "first", "second", "third", "fourth", "fifth",
    "also", "additionally", "furthermore", "moreover",
    "next", "then", "finally", "lastly",
    "one", "two", "three",
}

# Sentence-ending punctuation pattern
_SENTENCE_END = re.compile(r"[.!?]+$")


def align_narration_to_scenes(
    transcript: list[dict],
    scenes: list[dict],
) -> list[dict]:
    """Align transcript words to scene boundaries with phase classification.

    Args:
        transcript: List of word-level dicts from Whisper, each with keys:
            'word' (str), 'start' (float seconds), 'end' (float seconds).
        scenes: List of scene boundary dicts, each with keys:
            'start' (float seconds), 'end' (float seconds), and optionally
            'scene_id' (int/str).

    Returns:
        List of dicts (one per scene) with keys:
            scene_id: Scene identifier
            start, end: Scene time boundaries
            words: List of word dicts that overlap with this scene
            sentences: List of sentence strings
            wpm: Words per minute for this scene
            narration_phase: One of introducing, listing, concluding, explaining
    """
    if not transcript or not scenes:
        logger.warning("Empty transcript or scenes list")
        return []

    # Sort both by start time
    transcript = sorted(transcript, key=lambda w: w.get("start", 0))
    scenes = sorted(scenes, key=lambda s: s["start"])

    # Detect topic shifts using word groupings per scene
    scene_results = []
    word_idx = 0

    for scene_idx, scene in enumerate(scenes):
        s_start = scene["start"]
        s_end = scene["end"]
        scene_id = scene.get("scene_id", scene_idx)

        # Find words overlapping with this scene
        scene_words = []
        for word in transcript:
            w_start = word.get("start", 0)
            w_end = word.get("end", w_start)

            # Word overlaps scene if: word_start < scene_end AND word_end > scene_start
            if w_start < s_end and w_end > s_start:
                scene_words.append(word)

        # Group words into sentences
        sentences = _group_into_sentences(scene_words)

        # Compute words per minute
        duration = s_end - s_start
        wpm = (len(scene_words) / duration * 60.0) if duration > 0 else 0.0

        scene_results.append({
            "scene_id": scene_id,
            "start": s_start,
            "end": s_end,
            "words": scene_words,
            "sentences": sentences,
            "wpm": round(wpm, 1),
            "narration_phase": "explaining",  # default, updated below
        })

    # Classify narration phases
    _classify_phases(scene_results)

    return scene_results


def _group_into_sentences(words: list[dict]) -> list[str]:
    """Group word dicts into sentence strings based on punctuation."""
    if not words:
        return []

    sentences = []
    current = []

    for word in words:
        text = word.get("word", "").strip()
        if not text:
            continue
        current.append(text)

        if _SENTENCE_END.search(text):
            sentences.append(" ".join(current))
            current = []

    # Remaining words form a partial sentence
    if current:
        sentences.append(" ".join(current))

    return sentences


def _classify_phases(scene_results: list[dict]) -> None:
    """Classify narration phase for each scene in-place.

    Phases:
        introducing: first scene of a new topic (detected by embedding distance)
        listing: contains listing keywords
        concluding: last scene before a topic shift
        explaining: default
    """
    if not scene_results:
        return

    # Detect topic shifts using sentence text similarity
    topic_shift_indices = _detect_topic_shifts(scene_results)

    for i, result in enumerate(scene_results):
        words_lower = {w.get("word", "").strip().lower().rstrip(".,!?;:") for w in result["words"]}

        # Check for listing keywords
        if words_lower & _LISTING_KEYWORDS:
            result["narration_phase"] = "listing"
        # Check if this is the first scene of a new topic
        elif i in topic_shift_indices:
            result["narration_phase"] = "introducing"
        # Check if next scene is a topic shift (this is concluding)
        elif (i + 1) in topic_shift_indices:
            result["narration_phase"] = "concluding"
        else:
            result["narration_phase"] = "explaining"


def _detect_topic_shifts(scene_results: list[dict]) -> set[int]:
    """Detect topic shifts by computing text similarity between consecutive scenes.

    Uses simple bag-of-words cosine distance when sentence-transformers is not
    available, or sentence embeddings when it is.

    Returns:
        Set of scene indices where a new topic begins.
    """
    if len(scene_results) < 3:
        # First scene is always "introducing" if we have scenes
        return {0} if scene_results else set()

    # Always mark the first scene as a topic start
    shifts = {0}

    # Try sentence-transformers for embedding-based detection
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [" ".join(r["sentences"]) if r["sentences"] else "" for r in scene_results]
        embeddings = model.encode(texts, show_progress_bar=False)

        # Compute cosine distances between consecutive scenes
        distances = []
        for i in range(len(embeddings) - 1):
            a = embeddings[i]
            b = embeddings[i + 1]
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a < 1e-8 or norm_b < 1e-8:
                distances.append(1.0)
            else:
                sim = float(np.dot(a, b) / (norm_a * norm_b))
                distances.append(1.0 - sim)

        # Topic shift where distance exceeds threshold (mean + 1 std)
        if distances:
            threshold = float(np.mean(distances) + np.std(distances))
            for i, dist in enumerate(distances):
                if dist > threshold:
                    shifts.add(i + 1)

        logger.debug("Topic shifts detected at scenes: %s (embedding-based)", shifts)
        return shifts

    except ImportError:
        logger.info("sentence-transformers not available, using bag-of-words for topic detection")

    # Fallback: bag-of-words cosine distance
    scene_vocabs = []
    all_words_set: set[str] = set()
    for r in scene_results:
        words = set()
        for w in r["words"]:
            token = w.get("word", "").strip().lower().rstrip(".,!?;:")
            if len(token) > 2:
                words.add(token)
                all_words_set.add(token)
        scene_vocabs.append(words)

    vocab_list = sorted(all_words_set)
    vocab_idx = {w: i for i, w in enumerate(vocab_list)}

    def to_vector(word_set: set[str]) -> np.ndarray:
        vec = np.zeros(len(vocab_list), dtype=np.float32)
        for w in word_set:
            if w in vocab_idx:
                vec[vocab_idx[w]] = 1.0
        return vec

    vectors = [to_vector(v) for v in scene_vocabs]

    distances = []
    for i in range(len(vectors) - 1):
        a, b = vectors[i], vectors[i + 1]
        norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
        if norm_a < 1e-8 or norm_b < 1e-8:
            distances.append(1.0)
        else:
            sim = float(np.dot(a, b) / (norm_a * norm_b))
            distances.append(1.0 - sim)

    if distances:
        threshold = float(np.mean(distances) + np.std(distances))
        for i, dist in enumerate(distances):
            if dist > threshold:
                shifts.add(i + 1)

    logger.debug("Topic shifts detected at scenes: %s (bag-of-words)", shifts)
    return shifts

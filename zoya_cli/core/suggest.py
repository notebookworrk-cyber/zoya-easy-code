"""Fuzzy command/option suggestion engine.

Used to turn a mistyped command (e.g. ``zoya biuld``) into a helpful
suggestion (``build``). Implements a light-weight edit-distance metric that is
good enough for short command names and fast enough to run on every dispatch.
"""

from __future__ import annotations

from typing import Iterable, Sequence


def _levenshtein(a: str, b: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def suggest(word: str, candidates: Iterable[str], *, max_distance: int = 3) -> list[str]:
    """Return candidate names within ``max_distance`` of ``word``, best first."""
    scored: list[tuple[int, str]] = []
    for cand in candidates:
        # Prefer prefix matches strongly.
        if cand.startswith(word):
            scored.append((0, cand))
            continue
        if word and cand and word[0] == cand[0]:
            d = _levenshtein(word, cand)
            if d <= max_distance:
                scored.append((d, cand))
            continue
        d = _levenshtein(word, cand)
        if d <= max(1, max_distance - 1):
            scored.append((d + 1, cand))
    scored.sort(key=lambda t: (t[0], t[1]))
    seen: set[str] = set()
    out: list[str] = []
    for _, cand in scored:
        if cand not in seen:
            seen.add(cand)
            out.append(cand)
    return out[:5]


def did_you_mean(word: str, candidates: Sequence[str]) -> str | None:
    """Return the single best suggestion, or ``None``."""
    suggestions = suggest(word, candidates)
    return suggestions[0] if suggestions else None

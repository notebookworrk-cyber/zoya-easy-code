from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import secrets, time
from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class UpdateStrategy(str, Enum):
    BEST = "best"
    LATEST = "latest"
    SUM = "sum"
    AVERAGE = "average"


class ResetPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


@dataclass
class LeaderboardEntry:
    rank: int
    user_id: str
    username: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    updated_at: float = 0.0


@dataclass
class LeaderboardDefinition:
    id: str
    name: str
    sort_order: SortOrder = SortOrder.DESC
    update_strategy: UpdateStrategy = UpdateStrategy.BEST
    reset_period: ResetPeriod = ResetPeriod.NEVER
    max_entries: Optional[int] = None


class LeaderboardError(Exception):
    def __init__(self, message: str, code: str = "LEADERBOARD_ERROR"):
        self.code = code
        super().__init__(message)


_MOCK_USERNAMES: Dict[str, str] = {
    "user_alice": "Alice",
    "user_bob": "Bob",
    "user_charlie": "Charlie",
    "user_diana": "Diana",
    "user_eve": "Eve",
    "user_frank": "Frank",
    "user_grace": "Grace",
    "user_henry": "Henry",
    "user_iris": "Iris",
    "user_jack": "Jack",
}


def _get_username(user_id: str) -> str:
    return _MOCK_USERNAMES.get(user_id, user_id)


def _default_metadata() -> Optional[Dict[str, Any]]:
    return None


class LeaderboardService:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self._definitions: Dict[str, LeaderboardDefinition] = {}
        self._scores: Dict[str, Dict[str, float]] = {}
        self._metadata: Dict[str, Dict[str, Optional[Dict[str, Any]]]] = {}
        self._timestamps: Dict[str, Dict[str, float]] = {}
        self._submission_counts: Dict[str, Dict[str, int]] = {}

    def _compute_score(
        self,
        leaderboard_id: str,
        user_id: str,
        new_score: float,
        strategy: UpdateStrategy,
    ) -> float:
        current = self._scores.get(leaderboard_id, {}).get(user_id)
        if current is None:
            return new_score
        if strategy == UpdateStrategy.BEST:
            return max(current, new_score)
        elif strategy == UpdateStrategy.LATEST:
            return new_score
        elif strategy == UpdateStrategy.SUM:
            return current + new_score
        elif strategy == UpdateStrategy.AVERAGE:
            count = self._submission_counts.get(leaderboard_id, {}).get(user_id, 1)
            total = current * (count - 1) + new_score
            return total / count
        return new_score

    def _sorted_entries(self, leaderboard_id: str) -> List[LeaderboardEntry]:
        definition = self._definitions.get(leaderboard_id)
        if definition is None:
            return []

        scores = self._scores.get(leaderboard_id, {})
        reverse = definition.sort_order == SortOrder.DESC
        sorted_users = sorted(scores.items(), key=lambda x: x[1], reverse=reverse)

        entries = []
        for rank, (uid, score) in enumerate(sorted_users, start=1):
            if definition.max_entries and rank > definition.max_entries:
                break
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=uid,
                    username=_get_username(uid),
                    score=score,
                    metadata=self._metadata.get(leaderboard_id, {}).get(uid),
                    updated_at=self._timestamps.get(leaderboard_id, {}).get(uid, 0.0),
                )
            )
        return entries

    def submit_score(
        self,
        leaderboard_id: str,
        user_id: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LeaderboardEntry:
        if leaderboard_id not in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{leaderboard_id}' not found", code="NOT_FOUND"
            )

        definition = self._definitions[leaderboard_id]
        now = time.time()

        if leaderboard_id not in self._scores:
            self._scores[leaderboard_id] = {}
            self._metadata[leaderboard_id] = {}
            self._timestamps[leaderboard_id] = {}
            self._submission_counts[leaderboard_id] = {}

        if user_id not in self._submission_counts[leaderboard_id]:
            self._submission_counts[leaderboard_id][user_id] = 0
        self._submission_counts[leaderboard_id][user_id] += 1

        new_score = self._compute_score(
            leaderboard_id, user_id, score, definition.update_strategy
        )
        self._scores[leaderboard_id][user_id] = new_score
        self._timestamps[leaderboard_id][user_id] = now

        if metadata is not None:
            existing = self._metadata[leaderboard_id].get(user_id)
            if existing is None:
                self._metadata[leaderboard_id][user_id] = metadata
            else:
                existing.update(metadata)

        entries = self._sorted_entries(leaderboard_id)
        for entry in entries:
            if entry.user_id == user_id:
                return entry

        return LeaderboardEntry(
            rank=len(entries) + 1,
            user_id=user_id,
            username=_get_username(user_id),
            score=new_score,
            metadata=metadata,
            updated_at=now,
        )

    def get_scores(
        self, leaderboard_id: str, limit: int = 50, offset: int = 0
    ) -> List[LeaderboardEntry]:
        entries = self._sorted_entries(leaderboard_id)
        return entries[offset : offset + limit]

    def get_rank(
        self, leaderboard_id: str, user_id: str
    ) -> Optional[LeaderboardEntry]:
        entries = self._sorted_entries(leaderboard_id)
        for entry in entries:
            if entry.user_id == user_id:
                return entry
        return None

    def get_around_user(
        self, leaderboard_id: str, user_id: str, range: int = 3
    ) -> List[LeaderboardEntry]:
        entries = self._sorted_entries(leaderboard_id)
        for idx, entry in enumerate(entries):
            if entry.user_id == user_id:
                start = max(0, idx - range)
                end = min(len(entries), idx + range + 1)
                return entries[start:end]
        return []

    def get_friends_leaderboard(
        self, leaderboard_id: str, user_id: str
    ) -> List[LeaderboardEntry]:
        _mock_friends: Dict[str, List[str]] = {
            "user_alice": ["user_bob", "user_charlie"],
            "user_bob": ["user_alice", "user_diana"],
            "user_charlie": ["user_alice", "user_eve"],
            "user_diana": ["user_bob", "user_frank"],
            "user_eve": ["user_charlie", "user_grace"],
            "user_frank": ["user_diana", "user_henry"],
            "user_grace": ["user_eve", "user_iris"],
            "user_henry": ["user_frank", "user_jack"],
            "user_iris": ["user_grace"],
            "user_jack": ["user_henry"],
        }
        friends = set(_mock_friends.get(user_id, []))
        friends.add(user_id)
        entries = self._sorted_entries(leaderboard_id)
        return [e for e in entries if e.user_id in friends]

    def create_leaderboard(self, definition: LeaderboardDefinition) -> None:
        if definition.id in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{definition.id}' already exists", code="CONFLICT"
            )
        self._definitions[definition.id] = definition
        self._scores[definition.id] = {}
        self._metadata[definition.id] = {}
        self._timestamps[definition.id] = {}
        self._submission_counts[definition.id] = {}

    def update_leaderboard(self, id: str, updates: dict) -> None:
        if id not in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{id}' not found", code="NOT_FOUND"
            )
        definition = self._definitions[id]
        for key, value in updates.items():
            if hasattr(definition, key):
                setattr(definition, key, value)

    def delete_leaderboard(self, id: str) -> None:
        if id not in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{id}' not found", code="NOT_FOUND"
            )
        del self._definitions[id]
        self._scores.pop(id, None)
        self._metadata.pop(id, None)
        self._timestamps.pop(id, None)
        self._submission_counts.pop(id, None)

    def list_leaderboards(self) -> List[LeaderboardDefinition]:
        return list(self._definitions.values())

    def reset_leaderboard(self, id: str) -> None:
        if id not in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{id}' not found", code="NOT_FOUND"
            )
        self._scores[id] = {}
        self._metadata[id] = {}
        self._timestamps[id] = {}
        self._submission_counts[id] = {}

    def get_reset_schedule(self, id: str) -> Optional[str]:
        if id not in self._definitions:
            raise LeaderboardError(
                f"Leaderboard '{id}' not found", code="NOT_FOUND"
            )
        period = self._definitions[id].reset_period
        if period == ResetPeriod.NEVER:
            return None
        return period.value

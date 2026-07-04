import copy
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MatchStatus(str, Enum):
    WAITING = "waiting"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LobbyStatus(str, Enum):
    OPEN = "open"
    IN_MATCH = "in_match"
    CLOSED = "closed"


@dataclass
class MatchConfig:
    max_players: int = 4
    min_players: int = 2
    timeout: float = 30.0
    ranked: bool = False
    region: str = "us-east"
    custom_data: dict[str, Any] | None = None


@dataclass
class Match:
    id: str
    players: list[str] = field(default_factory=list)
    status: MatchStatus = MatchStatus.WAITING
    config: MatchConfig | None = None
    created_at: float = 0.0
    started_at: float | None = None
    ended_at: float | None = None
    winner_id: str | None = None
    server_endpoint: str | None = None


@dataclass
class LobbyPlayer:
    user_id: str
    username: str
    ready: bool = False
    party_id: str | None = None


@dataclass
class Lobby:
    id: str
    name: str
    players: list[LobbyPlayer] = field(default_factory=list)
    config: MatchConfig | None = None
    status: LobbyStatus = LobbyStatus.OPEN
    host_user_id: str | None = None


class MultiplayerError(Exception):
    def __init__(self, message: str, code: str = "MULTIPLAYER_ERROR"):
        self.code = code
        super().__init__(message)


_MOCK_USERNAMES: dict[str, str] = {
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


class MultiplayerService:
    def __init__(self, base_url: str, api_key: str, realtime):
        self.base_url = base_url
        self.api_key = api_key
        self._realtime = realtime
        self._matches: dict[str, Match] = {}
        self._lobbies: dict[str, Lobby] = {}
        self._matchmaking_queue: list[str] = []
        self._parties: dict[str, set[str]] = {}
        self._player_parties: dict[str, str] = {}
        self._state: dict[str, Any] = {}
        self._state_listeners: dict[str, list[Callable]] = {}
        self._event_handlers: dict[str, list[Callable]] = {}
        self._player_lobby: dict[str, str] = {}
        self._player_match: dict[str, str] = {}
        self._matchmaking_users: set[str] = set()

    def find_match(self, config: MatchConfig) -> Match:
        if not self._matchmaking_queue:
            self._matchmaking_queue.append("user_alice")
            self._matchmaking_users.add("user_alice")

        compatible = [uid for uid in self._matchmaking_queue if uid != "user_alice"]
        if compatible:
            opponent = compatible[0]
            self._matchmaking_queue.remove(opponent)
            self._matchmaking_users.discard(opponent)
            self._matchmaking_users.discard("user_alice")
            self._matchmaking_queue.remove("user_alice")

            match = Match(
                id=secrets.token_hex(8),
                players=["user_alice", opponent],
                status=MatchStatus.IN_PROGRESS,
                config=config,
                created_at=time.time(),
                started_at=time.time(),
                server_endpoint=f"{self.base_url}/match/{secrets.token_hex(4)}",
            )
            self._matches[match.id] = match
            for uid in match.players:
                self._player_match[uid] = match.id
            return match

        self._matchmaking_queue.append("user_alice")
        self._matchmaking_users.add("user_alice")

        return Match(
            id="pending",
            players=["user_alice"],
            status=MatchStatus.WAITING,
            config=config,
            created_at=time.time(),
        )

    def cancel_matchmaking(self) -> None:
        self._matchmaking_queue[:] = [
            u for u in self._matchmaking_queue if u != "user_alice"
        ]
        self._matchmaking_users.discard("user_alice")

    def get_match(self, match_id: str) -> Match:
        match = self._matches.get(match_id)
        if match is None:
            raise MultiplayerError(
                f"Match '{match_id}' not found", code="MATCH_NOT_FOUND"
            )
        return copy.deepcopy(match)

    def leave_match(self, match_id: str) -> None:
        match = self._matches.get(match_id)
        if match is None:
            raise MultiplayerError(
                f"Match '{match_id}' not found", code="MATCH_NOT_FOUND"
            )
        match.status = MatchStatus.CANCELLED
        match.ended_at = time.time()
        for uid in match.players:
            self._player_match.pop(uid, None)

    def create_lobby(self, name: str, config: MatchConfig) -> Lobby:
        lobby_id = secrets.token_hex(8)
        lobby = Lobby(
            id=lobby_id,
            name=name,
            config=config,
            host_user_id="user_alice",
        )
        self._lobbies[lobby_id] = lobby
        return lobby

    def join_lobby(self, lobby_id: str) -> Lobby:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MultiplayerError(
                f"Lobby '{lobby_id}' not found", code="LOBBY_NOT_FOUND"
            )
        if lobby.status != LobbyStatus.OPEN:
            raise MultiplayerError("Lobby is not open", code="LOBBY_CLOSED")

        party_id = self._player_parties.get("user_alice")
        player = LobbyPlayer(
            user_id="user_alice",
            username=_get_username("user_alice"),
            party_id=party_id,
        )
        lobby.players.append(player)
        self._player_lobby["user_alice"] = lobby_id
        return lobby

    def leave_lobby(self, lobby_id: str) -> None:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MultiplayerError(
                f"Lobby '{lobby_id}' not found", code="LOBBY_NOT_FOUND"
            )
        lobby.players = [p for p in lobby.players if p.user_id != "user_alice"]
        self._player_lobby.pop("user_alice", None)

    def get_lobby(self, lobby_id: str) -> Lobby:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MultiplayerError(
                f"Lobby '{lobby_id}' not found", code="LOBBY_NOT_FOUND"
            )
        return copy.deepcopy(lobby)

    def list_lobbies(self) -> list[Lobby]:
        return [copy.deepcopy(l) for l in self._lobbies.values()]

    def set_ready(self, lobby_id: str, ready: bool) -> None:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MultiplayerError(
                f"Lobby '{lobby_id}' not found", code="LOBBY_NOT_FOUND"
            )
        for player in lobby.players:
            if player.user_id == "user_alice":
                player.ready = ready
                return
        raise MultiplayerError("User not in lobby", code="USER_NOT_IN_LOBBY")

    def start_match(self, lobby_id: str) -> Match:
        lobby = self._lobbies.get(lobby_id)
        if lobby is None:
            raise MultiplayerError(
                f"Lobby '{lobby_id}' not found", code="LOBBY_NOT_FOUND"
            )
        if lobby.host_user_id != "user_alice":
            raise MultiplayerError("Only the host can start a match", code="NOT_HOST")

        ready_count = sum(1 for p in lobby.players if p.ready)
        min_players = lobby.config.min_players if lobby.config else 2
        if ready_count < min_players:
            raise MultiplayerError(
                f"Not enough ready players ({ready_count}/{min_players})",
                code="NOT_ENOUGH_PLAYERS",
            )

        match = Match(
            id=secrets.token_hex(8),
            players=[p.user_id for p in lobby.players],
            status=MatchStatus.IN_PROGRESS,
            config=lobby.config,
            created_at=time.time(),
            started_at=time.time(),
            server_endpoint=f"{self.base_url}/match/{secrets.token_hex(4)}",
        )
        self._matches[match.id] = match
        lobby.status = LobbyStatus.IN_MATCH
        return match

    def create_party(self) -> str:
        party_id = secrets.token_hex(8)
        self._parties[party_id] = {"user_alice"}
        self._player_parties["user_alice"] = party_id
        return party_id

    def join_party(self, party_id: str) -> None:
        if party_id not in self._parties:
            self._parties[party_id] = set()
        self._parties[party_id].add("user_alice")
        self._player_parties["user_alice"] = party_id

    def leave_party(self) -> None:
        party_id = self._player_parties.pop("user_alice", None)
        if party_id and party_id in self._parties:
            self._parties[party_id].discard("user_alice")
            if not self._parties[party_id]:
                del self._parties[party_id]

    def invite_to_party(self, user_id: str) -> None:
        party_id = self._player_parties.get("user_alice")
        if party_id is None:
            raise MultiplayerError("User is not in a party", code="NO_PARTY")

    def sync_state(self, match_id: str, state: Any) -> None:
        self._state[match_id] = state
        for callback in self._state_listeners.get(match_id, []):
            callback(state)

    def get_state(self, match_id: str) -> Any:
        return copy.deepcopy(self._state.get(match_id))

    def on_state_change(self, match_id: str, callback: Callable) -> None:
        if match_id not in self._state_listeners:
            self._state_listeners[match_id] = []
        self._state_listeners[match_id].append(callback)

    def send_event(self, match_id: str, event: str, data: Any = None) -> None:
        for callback in self._event_handlers.get(f"{match_id}:{event}", []):
            callback(data)
        for callback in self._event_handlers.get(f"{match_id}:*", []):
            callback({"event": event, "data": data})

    def on_event(self, match_id: str, event_type: str, callback: Callable) -> None:
        key = f"{match_id}:{event_type}"
        if key not in self._event_handlers:
            self._event_handlers[key] = []
        self._event_handlers[key].append(callback)

"""Zoya Cloud Platform — client SDK.

Provides the ZoyaCloud client class and re-exports all public types,
services, and exceptions from the platform's seven service modules.
"""

from __future__ import annotations

from typing import Any

from .analytics import (
    AnalyticsError,
    AnalyticsEvent,
    AnalyticsQuery,
    AnalyticsResult,
    AnalyticsService,
    UserSession,
)
from .auth import (
    AUTH_DEFAULTS,
    AuthConfig,
    AuthError,
    AuthService,
    AuthSession,
    AuthUser,
)
from .database import (
    CollectionSchema,
    DatabaseError,
    DatabaseService,
    DocumentReference,
    FieldType,
    QueryFilter,
    QueryOperator,
    QueryOptions,
    QueryOrder,
    QueryResult,
    SortDirection,
)
from .leaderboard import (
    LeaderboardDefinition,
    LeaderboardEntry,
    LeaderboardError,
    LeaderboardService,
    ResetPeriod,
    SortOrder,
    UpdateStrategy,
)
from .multiplayer import (
    Lobby,
    LobbyPlayer,
    LobbyStatus,
    Match,
    MatchConfig,
    MatchStatus,
    MultiplayerError,
    MultiplayerService,
)
from .realtime import (
    Callback,
    ErrorCallback,
    PresenceCallback,
    PresenceInfo,
    RealtimeChannelInfo,
    RealtimeError,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeService,
)
from .storage import (
    StorageError,
    StorageObject,
    StorageService,
    UploadOptions,
    UploadResult,
)

__version__ = "0.1.0"


CLOUD_DEFAULTS: dict[str, Any] = {
    "project_id": "",
    "api_key": "",
    "region": "us-east",
    "base_url": "https://api.zoya.dev",
    "timeout": 10.0,
    "retry_count": 3,
}


class CloudConfig:
    project_id: str = ""
    api_key: str = ""
    region: str = "us-east"
    base_url: str = "https://api.zoya.dev"
    timeout: float = 10.0
    retry_count: int = 3


class ZoyaCloud:
    """Main client for the Zoya Cloud Platform.

    Wraps all seven cloud services (auth, database, storage, realtime,
    leaderboard, multiplayer, analytics) behind a single configurable
    interface.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        merged = dict(CLOUD_DEFAULTS)
        if config is not None:
            merged.update(config)
        self._config = merged
        self._connected = False

        base_url = self._config["base_url"]
        api_key = self._config["api_key"]

        self.auth = AuthService()
        self.database = DatabaseService(base_url, api_key)
        self.storage = StorageService(base_url, api_key)
        self.realtime = RealtimeService(base_url, api_key)
        self.leaderboard = LeaderboardService(base_url, api_key)
        self.multiplayer = MultiplayerService(base_url, api_key, self.realtime)
        self.analytics = AnalyticsService(base_url, api_key)

    async def connect(self) -> None:
        """Validate the API key and connect the realtime service."""
        if not self._config.get("api_key"):
            raise ValueError("API key is required to connect")
        self._connected = True
        self.realtime.connect()

    async def disconnect(self) -> None:
        """Disconnect the realtime service."""
        self._connected = False
        self.realtime.disconnect()

    def is_connected(self) -> bool:
        return self._connected

    def get_config(self) -> dict[str, Any]:
        return dict(self._config)

    def update_config(self, config: dict[str, Any]) -> None:
        self._config.update(config)


def create_cloud(config: dict[str, Any] | None = None) -> ZoyaCloud:
    """Factory function — creates and returns a ZoyaCloud instance."""
    return ZoyaCloud(config)


__all__ = [
    # analytics
    "AnalyticsError",
    "AnalyticsEvent",
    "AnalyticsQuery",
    "AnalyticsResult",
    "AnalyticsService",
    "UserSession",
    # auth
    "AUTH_DEFAULTS",
    "AuthConfig",
    "AuthError",
    "AuthService",
    "AuthSession",
    "AuthUser",
    # database
    "CollectionSchema",
    "DatabaseError",
    "DatabaseService",
    "DocumentReference",
    "FieldType",
    "QueryFilter",
    "QueryOperator",
    "QueryOptions",
    "QueryOrder",
    "QueryResult",
    "SortDirection",
    # leaderboard
    "LeaderboardDefinition",
    "LeaderboardEntry",
    "LeaderboardError",
    "LeaderboardService",
    "ResetPeriod",
    "SortOrder",
    "UpdateStrategy",
    # multiplayer
    "Lobby",
    "LobbyPlayer",
    "LobbyStatus",
    "Match",
    "MatchConfig",
    "MatchStatus",
    "MultiplayerError",
    "MultiplayerService",
    # realtime
    "Callback",
    "ErrorCallback",
    "PresenceCallback",
    "PresenceInfo",
    "RealtimeChannelInfo",
    "RealtimeError",
    "RealtimeEvent",
    "RealtimeEventType",
    "RealtimeService",
    # storage
    "StorageError",
    "StorageObject",
    "StorageService",
    "UploadOptions",
    "UploadResult",
    # package-level
    "CloudConfig",
    "ZoyaCloud",
    "create_cloud",
]

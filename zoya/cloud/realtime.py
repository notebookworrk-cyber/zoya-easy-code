import contextlib
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RealtimeEventType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    PRESENCE = "presence"
    DATA_CHANGE = "data_change"
    ERROR = "error"


@dataclass
class RealtimeEvent:
    type: RealtimeEventType
    channel: str
    data: Any = None
    timestamp: float = 0.0
    sender: str | None = None


@dataclass
class RealtimeChannelInfo:
    name: str
    subscribers: int = 0
    ephemeral: bool = False


@dataclass
class PresenceInfo:
    user_id: str
    username: str
    status: str = "online"
    last_seen: float = 0.0
    metadata: dict[str, Any] | None = None


class RealtimeError(Exception):
    def __init__(self, message: str, code: str = "REALTIME_ERROR"):
        self.code = code
        super().__init__(message)


Callback = Callable[[RealtimeEvent], None]
PresenceCallback = Callable[[list[PresenceInfo]], None]
ErrorCallback = Callable[[Exception], None]


class RealtimeService:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._connected = False
        self._channel_subscribers: dict[str, list[Callback]] = {}
        self._presence_callbacks: dict[str, list[PresenceCallback]] = {}
        self._presence_store: dict[str, dict[str, PresenceInfo]] = {}
        self._global_event_listeners: list[Callback] = []
        self._global_error_listeners: list[ErrorCallback] = []
        self._reconnect_max_attempts: int = 5
        self._reconnect_interval: float = 2.0
        self._reconnect_attempts: int = 0
        self._lock = threading.Lock()

    def connect(self):
        with self._lock:
            self._connected = True
            self._reconnect_attempts = 0
        self._dispatch(
            RealtimeEvent(
                type=RealtimeEventType.CONNECT,
                channel="system",
                data={"base_url": self._base_url},
                timestamp=time.time(),
            )
        )

    def disconnect(self):
        with self._lock:
            self._connected = False
        self._dispatch(
            RealtimeEvent(
                type=RealtimeEventType.DISCONNECT,
                channel="system",
                data={"base_url": self._base_url},
                timestamp=time.time(),
            )
        )

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, channel: str, callback: Callback):
        with self._lock:
            if channel not in self._channel_subscribers:
                self._channel_subscribers[channel] = []
                self._presence_store[channel] = {}
                self._presence_callbacks[channel] = []
            self._channel_subscribers[channel].append(callback)

    def unsubscribe(
        self,
        channel: str,
        callback: Callback | None = None,
    ):
        with self._lock:
            if channel not in self._channel_subscribers:
                return
            if callback is None:
                self._channel_subscribers[channel] = []
            else:
                self._channel_subscribers[channel] = [
                    cb
                    for cb in self._channel_subscribers[channel]
                    if cb is not callback
                ]
            if not self._channel_subscribers[channel]:
                del self._channel_subscribers[channel]
                self._presence_store.pop(channel, None)
                self._presence_callbacks.pop(channel, None)

    def publish(self, channel: str, data: Any):
        if not self._connected:
            raise RealtimeError("Cannot publish: not connected", "NOT_CONNECTED")
        event = RealtimeEvent(
            type=RealtimeEventType.MESSAGE,
            channel=channel,
            data=data,
            timestamp=time.time(),
        )
        self._dispatch(event)

    def update_presence(
        self,
        status: str,
        metadata: dict[str, Any] | None = None,
        user_id: str = "anonymous",
        username: str = "anonymous",
    ):
        if not self._connected:
            raise RealtimeError(
                "Cannot update presence: not connected", "NOT_CONNECTED"
            )
        now = time.time()
        info = PresenceInfo(
            user_id=user_id,
            username=username,
            status=status,
            last_seen=now,
            metadata=metadata,
        )
        with self._lock:
            for channel in self._channel_subscribers:
                self._presence_store.setdefault(channel, {})[user_id] = info
                presence_list = list(self._presence_store.get(channel, {}).values())
                event = RealtimeEvent(
                    type=RealtimeEventType.PRESENCE,
                    channel=channel,
                    data=presence_list,
                    timestamp=now,
                )
        self._dispatch(event)

        with self._lock:
            for channel in self._channel_subscribers:
                if channel in self._presence_callbacks:
                    presence_list = list(self._presence_store.get(channel, {}).values())
                    for cb in self._presence_callbacks[channel]:
                        self._safe_call(cb, presence_list)

    def get_presence(self, channel: str) -> list[PresenceInfo]:
        return self._get_presence_list(channel)

    def _get_presence_list(self, channel: str) -> list[PresenceInfo]:
        with self._lock:
            store = self._presence_store.get(channel, {})
            return list(store.values())

    def on_presence_change(self, channel: str, callback: PresenceCallback):
        with self._lock:
            if channel not in self._presence_callbacks:
                self._presence_callbacks[channel] = []
            self._presence_callbacks[channel].append(callback)

    def list_channels(self) -> list[RealtimeChannelInfo]:
        results: list[RealtimeChannelInfo] = []
        with self._lock:
            for name, subs in self._channel_subscribers.items():
                results.append(
                    RealtimeChannelInfo(
                        name=name,
                        subscribers=len(subs),
                        ephemeral=False,
                    )
                )
        return results

    def get_channel_subscribers(self, channel: str) -> int:
        with self._lock:
            subs = self._channel_subscribers.get(channel, [])
            return len(subs)

    def set_reconnect_policy(self, max_attempts: int, interval: float):
        with self._lock:
            self._reconnect_max_attempts = max_attempts
            self._reconnect_interval = interval

    def on_event(self, callback: Callback):
        with self._lock:
            self._global_event_listeners.append(callback)

    def on_error(self, callback: ErrorCallback):
        with self._lock:
            self._global_error_listeners.append(callback)

    def _dispatch(self, event: RealtimeEvent):
        with self._lock:
            listeners = list(self._global_event_listeners)
            channel_subs = list(self._channel_subscribers.get(event.channel, []))
        for cb in listeners:
            self._safe_call(cb, event)
        for cb in channel_subs:
            self._safe_call(cb, event)

    def _safe_call(self, fn: Callable, *args: Any, **kwargs: Any):
        try:
            fn(*args, **kwargs)
        except Exception as e:
            with self._lock:
                err_listeners = list(self._global_error_listeners)
            for err_cb in err_listeners:
                with contextlib.suppress(Exception):
                    err_cb(e)

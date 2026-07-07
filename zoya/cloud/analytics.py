"""Cloud analytics service for tracking and reporting application metrics."""

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalyticsEvent:
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    user_id: str | None = None
    session_id: str | None = None
    timestamp: float = 0.0
    value: float | None = None


@dataclass
class AnalyticsQuery:
    event: str
    start_date: float
    end_date: float
    group_by: str | None = None
    metrics: list[str] = field(default_factory=lambda: ["count"])


@dataclass
class AnalyticsResult:
    event: str
    metrics: dict[str, float] = field(default_factory=dict)
    breakdown: dict[str, dict[str, float]] | None = None
    total: int = 0
    period: dict[str, float] | None = None


@dataclass
class UserSession:
    session_id: str
    user_id: str
    start_time: float = 0.0
    end_time: float | None = None
    duration: float = 0.0
    page_views: int = 0
    events_count: int = 0
    device: str | None = None
    os: str | None = None
    browser: str | None = None
    ip: str | None = None
    country: str | None = None


class AnalyticsError(Exception):
    def __init__(self, message: str, code: str = "ANALYTICS_ERROR"):
        self.code = code
        super().__init__(message)


class AnalyticsService:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self._session_id: str = secrets.token_hex(16)
        self._events: list[AnalyticsEvent] = []
        self._sessions: dict[str, UserSession] = {}
        self._active_sessions: dict[str, UserSession] = {}
        self._opted_out: set[str] = set()
        self._flush_interval: float = 30.0
        self._flush_timer: threading.Timer | None = None
        self._start_flush_timer()

    def _start_flush_timer(self) -> None:
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        self._flush_timer = threading.Timer(self._flush_interval, self.flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def track(
        self, event: str, properties: dict[str, Any] | None = None, value: float | None = None
    ) -> None:
        if self._session_id in self._opted_out:
            return
        evt = AnalyticsEvent(
            name=event,
            properties=properties or {},
            user_id="user_alice",
            session_id=self._session_id,
            timestamp=time.time(),
            value=value,
        )
        self._events.append(evt)
        if self._session_id in self._active_sessions:
            self._active_sessions[self._session_id].events_count += 1

    def track_page_view(self, page: str, duration: float | None = None) -> None:
        self.track("page_view", {"page": page, "duration": duration})
        if self._session_id in self._active_sessions:
            self._active_sessions[self._session_id].page_views += 1

    def track_error(self, error: str, fatal: bool = False) -> None:
        self.track("error", {"error": error, "fatal": fatal})

    def track_user_action(self, action: str, target: str | None = None) -> None:
        self.track("user_action", {"action": action, "target": target})

    def start_session(self) -> None:
        session = UserSession(
            session_id=self._session_id, user_id="user_alice", start_time=time.time()
        )
        self._active_sessions[self._session_id] = session
        self._sessions[self._session_id] = session
        self.track("session_start")

    def end_session(self) -> None:
        session = self._active_sessions.pop(self._session_id, None)
        if session is not None:
            session.end_time = time.time()
            session.duration = session.end_time - session.start_time
            self.track("session_end", {"duration": session.duration})

    def get_session_id(self) -> str:
        return self._session_id

    def flush(self) -> None:
        self._events.clear()

    def set_flush_interval(self, interval: float) -> None:
        self._flush_interval = interval
        self._start_flush_timer()

    def query(self, query: AnalyticsQuery) -> AnalyticsResult:
        filtered = [
            e
            for e in self._events
            if e.name == query.event and query.start_date <= e.timestamp <= query.end_date
        ]

        metrics: dict[str, float] = {}
        for m in query.metrics:
            if m == "count":
                metrics["count"] = float(len(filtered))
            elif m == "sum":
                metrics["sum"] = sum(e.value for e in filtered if e.value is not None)
            elif m == "avg":
                values = [e.value for e in filtered if e.value is not None]
                metrics["avg"] = sum(values) / len(values) if values else 0.0
            elif m == "min":
                values = [e.value for e in filtered if e.value is not None]
                metrics["min"] = min(values) if values else 0.0
            elif m == "max":
                values = [e.value for e in filtered if e.value is not None]
                metrics["max"] = max(values) if values else 0.0

        breakdown: dict[str, dict[str, float]] | None = None
        if query.group_by:
            groups: dict[str, list[AnalyticsEvent]] = {}
            for e in filtered:
                key = str(e.properties.get(query.group_by, "unknown"))
                if key not in groups:
                    groups[key] = []
                groups[key].append(e)
            breakdown = {}
            for key, group in groups.items():
                bm: dict[str, float] = {}
                for m in query.metrics:
                    if m == "count":
                        bm["count"] = float(len(group))
                    elif m == "sum":
                        bm["sum"] = sum(e.value for e in group if e.value is not None)
                    elif m == "avg":
                        vals = [e.value for e in group if e.value is not None]
                        bm["avg"] = sum(vals) / len(vals) if vals else 0.0
                breakdown[key] = bm

        return AnalyticsResult(
            event=query.event,
            metrics=metrics,
            breakdown=breakdown,
            total=len(filtered),
            period={"start": query.start_date, "end": query.end_date},
        )

    def get_event_count(self, event: str, start_date: float, end_date: float) -> int:
        return sum(
            1 for e in self._events if e.name == event and start_date <= e.timestamp <= end_date
        )

    def get_user_count(self, start_date: float, end_date: float) -> int:
        user_ids = set()
        for e in self._events:
            if start_date <= e.timestamp <= end_date and e.user_id:
                user_ids.add(e.user_id)
        return len(user_ids)

    def get_active_users(self, days: int = 7) -> int:
        cutoff = time.time() - days * 86400
        user_ids = set()
        for e in self._events:
            if e.timestamp >= cutoff and e.user_id:
                user_ids.add(e.user_id)
        return len(user_ids)

    def get_retention_rate(self, cohort: float, days_since_onboarding: int) -> float:
        cutoff = cohort + days_since_onboarding * 86400
        cohort_users = set()
        retained = 0
        for e in self._events:
            if e.timestamp >= cohort and e.user_id:
                cohort_users.add(e.user_id)
        for uid in cohort_users:
            for e in self._events:
                if e.user_id == uid and e.timestamp >= cutoff:
                    retained += 1
                    break
        return retained / len(cohort_users) if cohort_users else 0.0

    def get_sessions(self, user_id: str, limit: int = 10) -> list[UserSession]:
        user_sessions = [s for s in self._sessions.values() if s.user_id == user_id]
        user_sessions.sort(key=lambda s: s.start_time, reverse=True)
        return user_sessions[:limit]

    def get_dashboard(self, metrics: list[str]) -> dict[str, float]:
        result: dict[str, float] = {}
        time.time()
        for m in metrics:
            if m == "total_events":
                result[m] = float(len(self._events))
            elif m == "active_sessions":
                result[m] = float(len(self._active_sessions))
            elif m == "total_sessions":
                result[m] = float(len(self._sessions))
            elif m == "active_users_7d":
                result[m] = float(self.get_active_users(7))
            elif m == "active_users_30d":
                result[m] = float(self.get_active_users(30))
        return result

    def opt_out(self) -> None:
        self._opted_out.add(self._session_id)

    def opt_in(self) -> None:
        self._opted_out.discard(self._session_id)

    def delete_user_data(self, user_id: str) -> None:
        self._events = [e for e in self._events if e.user_id != user_id]
        self._sessions = {sid: s for sid, s in self._sessions.items() if s.user_id != user_id}
        self._active_sessions = {
            sid: s for sid, s in self._active_sessions.items() if s.user_id != user_id
        }

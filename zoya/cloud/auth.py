from dataclasses import dataclass, field, replace
from typing import Optional, Callable, Dict, List, Any, Set
import hashlib, secrets, time, threading


@dataclass
class AuthUser:
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    email_verified: bool = False
    created_at: float = 0.0
    last_login: float = 0.0
    roles: List[str] = field(default_factory=lambda: ["user"])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthSession:
    user_id: str
    token: str
    refresh_token: str
    expires_at: float
    device: Optional[str] = None


class AuthConfig:
    jwt_secret: Optional[str] = None
    session_duration: float = 3600.0
    max_sessions: int = 5
    require_email_verification: bool = False
    allow_anonymous: bool = True
    oauth_providers: List[str] = field(default_factory=list)


AUTH_DEFAULTS: Dict[str, Any] = {
    "session_duration": 3600.0,
    "max_sessions": 5,
    "require_email_verification": False,
    "allow_anonymous": True,
    "oauth_providers": [],
}


class AuthError(Exception):
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.code = code
        super().__init__(message)


def _generate_token() -> str:
    return secrets.token_hex(32)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:
    def __init__(self, config: Optional[AuthConfig] = None):
        merged = AUTH_DEFAULTS.copy()
        if config:
            for k, v in vars(config).items():
                if v is not None:
                    merged[k] = v
        self._config = merged
        self._current_user: Optional[AuthUser] = None
        self._current_session: Optional[AuthSession] = None
        self._token_refresh_timer: Optional[threading.Timer] = None
        self._state_callbacks: Set[Callable[[Optional[AuthUser]], None]] = set()
        self._users: Dict[str, AuthUser] = {}
        self._password_hashes: Dict[str, str] = {}
        self._sessions: Dict[str, AuthSession] = {}
        self._refresh_tokens: Dict[str, str] = {}
        self._email_tokens: Dict[str, str] = {}

    def _create_session(self, user_id: str) -> AuthSession:
        existing_tokens = [
            token for token, s in self._sessions.items() if s.user_id == user_id
        ]
        while len(existing_tokens) >= self._config["max_sessions"]:
            oldest = existing_tokens.pop(0)
            removed = self._sessions.get(oldest)
            if removed:
                self._refresh_tokens.pop(removed.refresh_token, None)
            self._sessions.pop(oldest, None)

        token = _generate_token()
        refresh_token = _generate_token()
        expires_at = time.time() + self._config["session_duration"]
        session = AuthSession(
            user_id=user_id,
            token=token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        self._sessions[token] = session
        self._refresh_tokens[refresh_token] = token
        self._current_session = session
        self._schedule_token_refresh(self._config["session_duration"])
        return replace(session)

    def _schedule_token_refresh(self, expires_in: float) -> None:
        self._clear_refresh_timer()
        refresh_at = max(expires_in - 60, 0)

        def _refresh():
            try:
                self.refresh_token()
            except Exception:
                self._current_session = None
                self._current_user = None
                self._notify_state_change()

        self._token_refresh_timer = threading.Timer(refresh_at, _refresh)
        self._token_refresh_timer.daemon = True
        self._token_refresh_timer.start()

    def _clear_refresh_timer(self) -> None:
        if self._token_refresh_timer:
            self._token_refresh_timer.cancel()
            self._token_refresh_timer = None

    def _notify_state_change(self) -> None:
        user = self.get_current_user()
        for cb in self._state_callbacks:
            cb(user)

    def register(
        self,
        email: str,
        password: str,
        username: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuthUser:
        for u in self._users.values():
            if u.email == email:
                raise AuthError("Email already registered", "DUPLICATE_EMAIL")
            if u.username == username:
                raise AuthError("Username already taken", "DUPLICATE_USERNAME")

        user_id = secrets.token_hex(8)
        now = time.time()
        password_hash = _hash_password(password)
        user = AuthUser(
            id=user_id,
            email=email,
            username=username,
            display_name=username,
            email_verified=not self._config["require_email_verification"],
            created_at=now,
            last_login=now,
            roles=["user"],
            metadata=metadata or {},
        )
        self._users[user_id] = user
        self._password_hashes[user_id] = password_hash
        self._current_user = replace(user)

        if self._config["require_email_verification"]:
            self._email_tokens[email] = _generate_token()

        self._notify_state_change()
        return replace(user)

    def login(self, email: str, password: str) -> AuthSession:
        found = None
        for u in self._users.values():
            if u.email == email:
                found = u
                break
        if not found:
            raise AuthError("Invalid email or password", "INVALID_CREDENTIALS")
        stored_hash = self._password_hashes.get(found.id)
        if stored_hash != _hash_password(password):
            raise AuthError("Invalid email or password", "INVALID_CREDENTIALS")

        session = self._create_session(found.id)
        updated = replace(found, last_login=time.time())
        self._users[found.id] = updated
        self._current_user = updated
        self._notify_state_change()
        return session

    def login_with_provider(self, provider: str, token: str) -> AuthSession:
        if provider not in self._config["oauth_providers"]:
            raise AuthError(
                f"OAuth provider not supported: {provider}", "UNSUPPORTED_PROVIDER"
            )

        mock_id = (
            f"oauth_{provider}_"
            f"{hashlib.sha256(token.encode()).hexdigest()[:12]}"
        )

        if mock_id not in self._users:
            now = time.time()
            user = AuthUser(
                id=mock_id,
                email=f"{mock_id}@{provider}.auth",
                username=f"{provider}_user_{mock_id[:6]}",
                display_name=f"{provider} User",
                email_verified=True,
                created_at=now,
                last_login=now,
                roles=["user"],
                metadata={"provider": provider},
            )
            self._users[mock_id] = user
            self._password_hashes[mock_id] = ""
            self._current_user = replace(user)
        else:
            stored = self._users[mock_id]
            stored.last_login = time.time()
            self._current_user = replace(stored)

        self._notify_state_change()
        return self._create_session(mock_id)

    def login_anonymously(self) -> AuthSession:
        if not self._config["allow_anonymous"]:
            raise AuthError("Anonymous login is disabled", "ANONYMOUS_DISABLED")

        user_id = f"anon_{secrets.token_hex(8)}"
        now = time.time()
        user = AuthUser(
            id=user_id,
            email="",
            username=f"guest_{user_id[:8]}",
            display_name="Guest",
            email_verified=False,
            created_at=now,
            last_login=now,
            roles=["guest"],
            metadata={},
        )
        self._users[user_id] = user
        self._password_hashes[user_id] = ""
        self._current_user = replace(user)
        self._notify_state_change()
        return self._create_session(user_id)

    def logout(self) -> None:
        if self._current_session:
            self._sessions.pop(self._current_session.token, None)
            self._refresh_tokens.pop(self._current_session.refresh_token, None)
        self._clear_refresh_timer()
        self._current_session = None
        self._current_user = None
        self._notify_state_change()

    def refresh_token(self) -> AuthSession:
        if not self._current_session:
            raise AuthError("No active session", "NO_SESSION")

        user_id = self._current_session.user_id
        user = self._users.get(user_id)
        if not user:
            raise AuthError("User not found", "USER_NOT_FOUND")

        self._sessions.pop(self._current_session.token, None)
        self._refresh_tokens.pop(self._current_session.refresh_token, None)
        session = self._create_session(user_id)
        self._current_session = session
        self._current_user = replace(user)
        self._notify_state_change()
        return session

    def validate_session(self) -> bool:
        if not self._current_session:
            return False
        if time.time() >= self._current_session.expires_at:
            return False
        stored = self._sessions.get(self._current_session.token)
        if not stored:
            return False
        return stored.user_id in self._users

    def get_current_user(self) -> Optional[AuthUser]:
        if not self._current_user:
            return None
        return replace(self._current_user)

    def is_authenticated(self) -> bool:
        return self._current_user is not None and self._current_session is not None

    def update_profile(self, data: Dict[str, Any]) -> AuthUser:
        if not self._current_user:
            raise AuthError("Not authenticated", "NOT_AUTHENTICATED")

        stored = self._users.get(self._current_user.id)
        if not stored:
            raise AuthError("User not found", "USER_NOT_FOUND")

        allowed = {"display_name", "avatar_url", "username"}
        for k, v in data.items():
            if k in allowed:
                setattr(stored, k, v)

        self._current_user = replace(stored)
        self._notify_state_change()
        return self.get_current_user()

    def change_password(self, old_password: str, new_password: str) -> None:
        if not self._current_user:
            raise AuthError("Not authenticated", "NOT_AUTHENTICATED")

        stored_hash = self._password_hashes.get(self._current_user.id)
        if stored_hash is None:
            raise AuthError("User not found", "USER_NOT_FOUND")
        if not stored_hash:
            raise AuthError(
                "Cannot change password for OAuth users", "OAUTH_USER"
            )
        if stored_hash != _hash_password(old_password):
            raise AuthError("Current password is incorrect", "INVALID_PASSWORD")

        self._password_hashes[self._current_user.id] = _hash_password(new_password)

    def reset_password(self, email: str) -> None:
        found = None
        for u in self._users.values():
            if u.email == email:
                found = u
                break
        if not found:
            return
        self._email_tokens[email] = _generate_token()

    def delete_account(self) -> None:
        if not self._current_user:
            raise AuthError("Not authenticated", "NOT_AUTHENTICATED")

        self._users.pop(self._current_user.id, None)
        self._password_hashes.pop(self._current_user.id, None)
        if self._current_session:
            self._sessions.pop(self._current_session.token, None)
            self._refresh_tokens.pop(self._current_session.refresh_token, None)
        self._clear_refresh_timer()
        self._current_session = None
        self._current_user = None
        self._notify_state_change()

    def send_verification_email(self) -> None:
        if not self._current_user:
            raise AuthError("Not authenticated", "NOT_AUTHENTICATED")
        if self._current_user.email_verified:
            raise AuthError("Email already verified", "ALREADY_VERIFIED")
        self._email_tokens[self._current_user.email] = _generate_token()

    def verify_email(self, token: str) -> bool:
        if not self._current_user:
            raise AuthError("Not authenticated", "NOT_AUTHENTICATED")

        stored = self._email_tokens.get(self._current_user.email)
        if not stored or stored != token:
            return False

        self._email_tokens.pop(self._current_user.email, None)
        stored_user = self._users.get(self._current_user.id)
        if stored_user:
            stored_user.email_verified = True
        self._current_user = replace(self._current_user, email_verified=True)
        self._notify_state_change()
        return True

    def get_token(self) -> Optional[str]:
        return self._current_session.token if self._current_session else None

    def on_auth_state_change(
        self, callback: Callable[[Optional[AuthUser]], None]
    ) -> None:
        self._state_callbacks.add(callback)

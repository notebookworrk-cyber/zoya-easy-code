"""Enterprise package with features for production-grade Zoya applications."""

__version__ = "0.1.0"

import json
import time
import uuid
from collections import defaultdict
from typing import Any


class EnterpriseError(Exception):
    pass


class Tenant:
    def __init__(self, name: str, plan: str = "free"):
        self.id: str = uuid.uuid4().hex[:12]
        self.name: str = name
        self.plan: str = plan
        self.settings: dict[str, Any] = {}
        self.created_at: float = time.time()
        self.is_active: bool = True
        self.max_users: int = 10
        self.max_storage_gb: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "plan": self.plan,
            "settings": self.settings,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
        }


class RBACManager:
    _built_in_roles = {
        "admin": ["*"],
        "editor": ["read", "write", "update"],
        "viewer": ["read"],
        "custom": [],
    }

    def __init__(self):
        self._roles: dict[str, list[str]] = dict(self._built_in_roles)
        self._assignments: dict[str, dict[str, str]] = defaultdict(dict)

    def create_role(self, name: str, permissions: list[str]) -> None:
        if name in self._roles:
            raise EnterpriseError(f"Role '{name}' already exists")
        self._roles[name] = list(permissions)

    def get_role(self, name: str) -> dict[str, Any] | None:
        perms = self._roles.get(name)
        if perms is None:
            return None
        return {"name": name, "permissions": perms, "built_in": name in self._built_in_roles}

    def update_role(self, name: str, permissions: list[str]) -> None:
        if name not in self._roles:
            raise EnterpriseError(f"Role '{name}' does not exist")
        self._roles[name] = list(permissions)

    def delete_role(self, name: str) -> None:
        if name in self._built_in_roles:
            raise EnterpriseError(f"Cannot delete built-in role '{name}'")
        self._roles.pop(name, None)
        for user_id in list(self._assignments.keys()):
            self._assignments[user_id] = {
                t: r for t, r in self._assignments[user_id].items() if r != name
            }

    def assign_role(self, user_id: str, role: str, tenant_id: str) -> None:
        if role not in self._roles:
            raise EnterpriseError(f"Role '{role}' does not exist")
        self._assignments[user_id][tenant_id] = role

    def remove_role(self, user_id: str, tenant_id: str) -> None:
        self._assignments[user_id].pop(tenant_id, None)

    def get_user_roles(self, user_id: str) -> list[str]:
        return list(self._assignments.get(user_id, {}).values())

    def check_permission(self, user_id: str, permission: str, tenant_id: str) -> bool:
        role_name = self._assignments.get(user_id, {}).get(tenant_id)
        if role_name is None:
            return False
        permissions = self._roles.get(role_name, [])
        if "*" in permissions:
            return True
        if permission in permissions:
            return True
        return bool(permission == "read" and "read" in permissions)

    def list_roles(self) -> list[str]:
        return list(self._roles.keys())


class AuditLog:
    def __init__(
        self,
        event: str,
        user_id: str,
        tenant_id: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
        ip_address: str = "",
        severity: str = "info",
    ):
        self.id: str = uuid.uuid4().hex[:12]
        self.event: str = event
        self.user_id: str = user_id
        self.tenant_id: str = tenant_id
        self.action: str = action
        self.resource: str = resource
        self.details: dict[str, Any] = details or {}
        self.ip_address: str = ip_address
        self.timestamp: float = time.time()
        self.severity: str = severity

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event": self.event,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp,
            "severity": self.severity,
        }


class AuditLogger:
    def __init__(self):
        self._logs: list[AuditLog] = []

    def log(
        self,
        event: str,
        user_id: str,
        tenant_id: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
        severity: str = "info",
    ) -> AuditLog:
        entry = AuditLog(
            event=event,
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            resource=resource,
            details=details,
            severity=severity,
        )
        self._logs.append(entry)
        return entry

    def query(self, filters: dict[str, Any]) -> list[AuditLog]:
        result = list(self._logs)
        for key, value in filters.items():
            if key == "user_id":
                result = [e for e in result if e.user_id == value]
            elif key == "tenant_id":
                result = [e for e in result if e.tenant_id == value]
            elif key == "action":
                result = [e for e in result if e.action == value]
            elif key == "event":
                result = [e for e in result if e.event == value]
            elif key == "severity":
                result = [e for e in result if e.severity == value]
            elif key == "start_time":
                result = [e for e in result if e.timestamp >= value]
            elif key == "end_time":
                result = [e for e in result if e.timestamp <= value]
            elif key == "resource":
                result = [e for e in result if e.resource == value]
        return result

    def get_by_user(self, user_id: str, limit: int = 50) -> list[AuditLog]:
        return [e for e in self._logs if e.user_id == user_id][-limit:]

    def get_by_tenant(self, tenant_id: str, limit: int = 50) -> list[AuditLog]:
        return [e for e in self._logs if e.tenant_id == tenant_id][-limit:]

    def get_recent(self, limit: int = 50) -> list[AuditLog]:
        return self._logs[-limit:]

    def export(self, format: str = "json") -> str:
        data = [e.to_dict() for e in self._logs]
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, indent=2, default=str)

    def clear(self) -> None:
        self._logs.clear()


class FeatureFlags:
    _default_flags = {
        "dark_mode": True,
        "beta_features": False,
        "analytics": True,
        "export_pdf": True,
        "multi_factor_auth": False,
    }

    def __init__(self):
        self._global_flags: dict[str, bool] = dict(self._default_flags)
        self._tenant_flags: dict[str, dict[str, bool]] = defaultdict(dict)

    def set_flag(self, name: str, enabled: bool, tenant_id: str | None = None) -> None:
        if tenant_id is None:
            self._global_flags[name] = enabled
        else:
            self._tenant_flags[tenant_id][name] = enabled

    def is_enabled(self, name: str, tenant_id: str | None = None) -> bool:
        if tenant_id is not None and name in self._tenant_flags.get(tenant_id, {}):
            return self._tenant_flags[tenant_id][name]
        return self._global_flags.get(name, False)

    def get_all(self, tenant_id: str | None = None) -> dict[str, bool]:
        flags = dict(self._global_flags)
        if tenant_id is not None:
            flags.update(self._tenant_flags.get(tenant_id, {}))
        return flags

    def delete_flag(self, name: str) -> None:
        self._global_flags.pop(name, None)
        for tf in self._tenant_flags.values():
            tf.pop(name, None)

    def list_flags(self) -> list[str]:
        return list(self._global_flags.keys())

    def reset(self, tenant_id: str | None = None) -> None:
        if tenant_id is None:
            self._global_flags = dict(self._default_flags)
            self._tenant_flags.clear()
        else:
            self._tenant_flags.pop(tenant_id, None)


class SSOProvider:
    _valid_names = {"google", "github", "microsoft", "okta", "custom"}

    def __init__(self, name: str, config: dict[str, str] | None = None):
        if name not in self._valid_names:
            raise EnterpriseError(
                f"Invalid SSO provider: {name}. Valid: {sorted(self._valid_names)}"
            )
        self.name: str = name
        self.config: dict[str, str] = config or {}
        self.is_configured: bool = bool(
            self.config.get("client_id") and self.config.get("client_secret")
        )

    def validate_config(self) -> list[str]:
        errors = []
        required = {"client_id", "client_secret"}
        if self.name != "custom":
            if "issuer" not in self.config:
                required.add("issuer")
        for field in required:
            if not self.config.get(field):
                errors.append(f"Missing required field: {field}")
        return errors


class SSOManager:
    def __init__(self):
        self._providers: dict[str, SSOProvider] = {}

    def add_provider(self, provider: SSOProvider) -> None:
        self._providers[provider.name] = provider

    def remove_provider(self, name: str) -> None:
        self._providers.pop(name, None)

    def get_provider(self, name: str) -> SSOProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[SSOProvider]:
        return list(self._providers.values())

    def generate_auth_url(self, provider: str, redirect_uri: str) -> str:
        prov = self._providers.get(provider)
        if prov is None:
            raise EnterpriseError(f"SSO provider '{provider}' not configured")
        issuer = prov.config.get("issuer", f"https://{provider}.com")
        client_id = prov.config.get("client_id", "")
        state = uuid.uuid4().hex[:16]
        return (
            f"{issuer}/oauth/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"state={state}&"
            f"scope=openid+profile+email"
        )

    def handle_callback(self, provider: str, code: str) -> dict[str, Any]:
        prov = self._providers.get(provider)
        if prov is None:
            raise EnterpriseError(f"SSO provider '{provider}' not configured")
        return {
            "access_token": f"mock_token_{uuid.uuid4().hex}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "provider": provider,
            "user": {
                "sub": uuid.uuid4().hex[:12],
                "email": f"user@{provider}.com",
                "name": f"SSO User ({provider})",
            },
        }

    def is_sso_enabled(self) -> bool:
        return any(p.is_configured for p in self._providers.values())


class TenantManager:
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def create_tenant(self, name: str, plan: str = "free") -> Tenant:
        if plan not in ("free", "pro", "enterprise"):
            raise EnterpriseError(f"Invalid plan: {plan}. Must be free, pro, or enterprise")
        tenant = Tenant(name=name, plan=plan)
        self._tenants[tenant.id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def update_tenant(self, tenant_id: str, updates: dict[str, Any]) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise EnterpriseError(f"Tenant '{tenant_id}' not found")
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
            elif key == "settings":
                tenant.settings.update(value)

    def delete_tenant(self, tenant_id: str) -> None:
        self._tenants.pop(tenant_id, None)

    def list_tenants(self) -> list[Tenant]:
        return list(self._tenants.values())

    def set_max_users(self, tenant_id: str, count: int) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise EnterpriseError(f"Tenant '{tenant_id}' not found")
        tenant.max_users = count

    def set_max_storage(self, tenant_id: str, gb: int) -> None:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise EnterpriseError(f"Tenant '{tenant_id}' not found")
        tenant.max_storage_gb = gb

    def get_usage(self, tenant_id: str) -> dict[str, Any]:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise EnterpriseError(f"Tenant '{tenant_id}' not found")
        return {"user_count": 0, "storage_gb": 0.0, "api_calls": 0, "tenant_id": tenant_id}


__all__ = [
    "EnterpriseError",
    "Tenant",
    "RBACManager",
    "AuditLog",
    "AuditLogger",
    "FeatureFlags",
    "SSOProvider",
    "SSOManager",
    "TenantManager",
]

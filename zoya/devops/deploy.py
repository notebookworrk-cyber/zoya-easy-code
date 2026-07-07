"""Deployment automation tools for releasing Zoya applications."""

from __future__ import annotations

import os
import shutil
import time
import uuid


class DeploymentConfig:
    name: str
    source: str
    target: str
    strategy: str
    health_check: str | None
    timeout: int = 300
    rollback_on_failure: bool = True
    environment: str
    env_vars: dict[str, str]

    def __init__(
        self,
        name: str,
        source: str,
        target: str,
        strategy: str = "rolling",
        health_check: str | None = None,
        timeout: int = 300,
        rollback_on_failure: bool = True,
        environment: str = "dev",
        env_vars: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.source = source
        self.target = target
        self.strategy = strategy
        self.health_check = health_check
        self.timeout = timeout
        self.rollback_on_failure = rollback_on_failure
        self.environment = environment
        self.env_vars = env_vars or {}


class Deployment:
    id: str
    config: DeploymentConfig
    version: str
    status: str
    started_at: float
    completed_at: float | None
    logs: list[str]

    def __init__(
        self,
        config: DeploymentConfig,
        version: str,
        id: str | None = None,
        status: str = "pending",
        started_at: float | None = None,
        completed_at: float | None = None,
        logs: list[str] | None = None,
    ) -> None:
        self.config = config
        self.version = version
        self.id = id or uuid.uuid4().hex[:12]
        self.status = status
        self.started_at = started_at or time.time()
        self.completed_at = completed_at
        self.logs = logs or []


class Deployer:
    _deployments: dict[str, Deployment]
    _environments: set

    def __init__(self) -> None:
        self._deployments = {}
        self._environments = {"dev", "staging", "production"}

    def deploy(self, config: DeploymentConfig, version: str | None = None) -> Deployment:
        ver = version or uuid.uuid4().hex[:8]
        deployment = Deployment(config=config, version=ver)
        deployment.status = "deploying"
        deployment.logs.append(
            f"[{deployment.id}] Deploying {config.name} v{ver} "
            f"to {config.environment} ({config.strategy})."
        )

        self._environments.add(config.environment)
        self._deployments[deployment.id] = deployment

        deployed = self._execute_deploy(deployment)
        self._deployments[deployment.id] = deployed

        if config.health_check and deployed.status == "healthy":
            healthy = self.health_check(config.health_check)
            if not healthy:
                deployed.logs.append(
                    f"[{deployment.id}] Health check failed at {config.health_check}."
                )
                if config.rollback_on_failure:
                    return self._do_rollback(deployed, "Health check failed")
                deployment.status = "failed"

        return deployed

    def _execute_deploy(self, deployment: Deployment) -> Deployment:
        config = deployment.config
        try:
            if config.strategy == "recreate":
                if os.path.isdir(config.target):
                    shutil.rmtree(config.target)
                os.makedirs(config.target, exist_ok=True)
            elif config.strategy in ("rolling", "blue_green", "canary"):
                os.makedirs(config.target, exist_ok=True)

            if os.path.isdir(config.source):
                for item in os.listdir(config.source):
                    src = os.path.join(config.source, item)
                    dst = os.path.join(config.target, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
            else:
                shutil.copy2(config.source, config.target)

            deployment.status = "healthy"
            deployment.logs.append(
                f"[{deployment.id}] Deployed {config.source} -> {config.target}."
            )
        except Exception as exc:
            deployment.status = "failed"
            deployment.logs.append(f"[{deployment.id}] Deploy failed: {exc}.")
            if config.rollback_on_failure:
                return self._do_rollback(deployment, str(exc))

        deployment.completed_at = time.time()
        return deployment

    def rollback(self, deployment_id: str) -> Deployment:
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise ValueError(f"Deployment '{deployment_id}' not found.")
        return self._do_rollback(deployment, "Manual rollback requested")

    def _do_rollback(self, deployment: Deployment, reason: str) -> Deployment:
        deployment.status = "rolled_back"
        deployment.logs.append(f"[{deployment.id}] Rolled back: {reason}.")
        deployment.completed_at = time.time()
        self._deployments[deployment.id] = deployment
        return deployment

    def get_deployment(self, id: str) -> Deployment | None:
        return self._deployments.get(id)

    def list_deployments(self, environment: str | None = None) -> list[Deployment]:
        if environment is None:
            return list(self._deployments.values())
        return [d for d in self._deployments.values() if d.config.environment == environment]

    def health_check(self, url: str) -> bool:
        import urllib.request

        try:
            resp = urllib.request.urlopen(url, timeout=10)
            return resp.status < 500
        except Exception:
            return False

    def switch_traffic(self, from_deploy: str, to_deploy: str, percentage: int = 100) -> None:
        src = self._deployments.get(from_deploy)
        dst = self._deployments.get(to_deploy)
        if src is None:
            raise ValueError(f"Source deployment '{from_deploy}' not found.")
        if dst is None:
            raise ValueError(f"Target deployment '{to_deploy}' not found.")

        pct = max(0, min(100, percentage))
        dst.logs.append(
            f"[{dst.id}] Traffic switched: {pct}% from '{src.config.name}' to '{dst.config.name}'."
        )

    def list_environments(self) -> list[str]:
        return sorted(self._environments)

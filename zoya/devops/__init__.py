"""Zoya DevOps — CI/CD pipeline and deployment management."""

from __future__ import annotations

from typing import Any, Dict

from .ci import (
    PipelineConfig,
    PipelineRun,
    PipelineRunner,
    PipelineStage,
    StageResult,
)
from .deploy import (
    Deployer,
    Deployment,
    DeploymentConfig,
)

__version__ = "0.1.0"


def create_pipeline(config: Dict[str, Any]) -> PipelineConfig:
    """Factory — create a PipelineConfig from a dictionary."""
    return PipelineConfig(
        name=config.get("name", ""),
        stages=list(config.get("stages", [])),
        environment=dict(config.get("environment", {})),
        timeout=int(config.get("timeout", 3600)),
        parallel=bool(config.get("parallel", False)),
    )


def create_deployment(config: Dict[str, Any]) -> DeploymentConfig:
    """Factory — create a DeploymentConfig from a dictionary."""
    return DeploymentConfig(
        name=config.get("name", ""),
        source=config.get("source", ""),
        target=config.get("target", ""),
        strategy=config.get("strategy", "rolling"),
        health_check=config.get("health_check"),
        timeout=int(config.get("timeout", 300)),
        rollback_on_failure=bool(config.get("rollback_on_failure", True)),
        environment=config.get("environment", "dev"),
        env_vars=dict(config.get("env_vars", {})),
    )


__all__ = [
    "__version__",
    "PipelineConfig",
    "PipelineRun",
    "PipelineRunner",
    "PipelineStage",
    "StageResult",
    "Deployer",
    "Deployment",
    "DeploymentConfig",
    "create_pipeline",
    "create_deployment",
]

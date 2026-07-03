from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional


class PipelineConfig:
    name: str
    stages: List[str]
    environment: Dict[str, str]
    timeout: int = 3600
    parallel: bool = False

    def __init__(
        self,
        name: str,
        stages: List[str],
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 3600,
        parallel: bool = False,
    ) -> None:
        self.name = name
        self.stages = stages
        self.environment = environment or {}
        self.timeout = timeout
        self.parallel = parallel


class PipelineStage:
    name: str
    commands: List[str]
    timeout: int = 300
    dependencies: List[str]
    artifacts: List[str]
    allow_failure: bool = False
    env: Dict[str, str]

    def __init__(
        self,
        name: str,
        commands: Optional[List[str]] = None,
        timeout: int = 300,
        dependencies: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        allow_failure: bool = False,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.commands = commands or []
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.artifacts = artifacts or []
        self.allow_failure = allow_failure
        self.env = env or {}


class StageResult:
    name: str
    status: str
    output: str
    exit_code: int
    started_at: float
    duration: float

    def __init__(
        self,
        name: str,
        status: str,
        output: str,
        exit_code: int,
        started_at: float,
        duration: float,
    ) -> None:
        self.name = name
        self.status = status
        self.output = output
        self.exit_code = exit_code
        self.started_at = started_at
        self.duration = duration


class PipelineRun:
    pipeline: PipelineConfig
    id: str
    status: str
    started_at: float
    finished_at: Optional[float]
    stage_results: List[StageResult]
    logs: List[str]

    def __init__(
        self,
        pipeline: PipelineConfig,
        id: Optional[str] = None,
        status: str = "pending",
        started_at: Optional[float] = None,
        finished_at: Optional[float] = None,
        stage_results: Optional[List[StageResult]] = None,
        logs: Optional[List[str]] = None,
    ) -> None:
        self.pipeline = pipeline
        self.id = id or uuid.uuid4().hex[:12]
        self.status = status
        self.started_at = started_at or time.time()
        self.finished_at = finished_at
        self.stage_results = stage_results or []
        self.logs = logs or []


class PipelineRunner:
    _runs: Dict[str, PipelineRun]
    _cancelled: set

    def __init__(self) -> None:
        self._runs = {}
        self._cancelled = set()

    def run(
        self, pipeline: PipelineConfig, env: Optional[Dict[str, str]] = None
    ) -> PipelineRun:
        merged_env = dict(pipeline.environment)
        if env is not None:
            merged_env.update(env)

        run = PipelineRun(pipeline=pipeline)
        self._runs[run.id] = run

        if pipeline.parallel:
            run = self._run_parallel(pipeline, merged_env, run)
        else:
            run = self._run_sequential(pipeline, merged_env, run)

        run.finished_at = time.time()
        return run

    def _run_sequential(
        self, pipeline: PipelineConfig, env: Dict[str, str], run: PipelineRun
    ) -> PipelineRun:
        run.status = "running"
        run.logs.append(f"[{run.id}] Pipeline '{pipeline.name}' started (sequential).")

        stage_map = self._resolve_stages(pipeline, env)
        overall_start = time.time()

        for stage_name in pipeline.stages:
            if run.id in self._cancelled:
                run.status = "cancelled"
                run.logs.append(f"[{run.id}] Pipeline cancelled.")
                return run

            elapsed = time.time() - overall_start
            if elapsed > pipeline.timeout:
                run.status = "failed"
                run.logs.append(f"[{run.id}] Pipeline timed out ({pipeline.timeout}s).")
                return run

            stage = stage_map.get(stage_name)
            if stage is None:
                run.logs.append(
                    f"[{run.id}] Stage '{stage_name}' not found — skipping."
                )
                continue

            result = self.run_stage(stage, env)
            run.stage_results.append(result)
            run.logs.append(
                f"[{run.id}] Stage '{stage.name}' -> {result.status} "
                f"(exit={result.exit_code}, {result.duration:.2f}s)"
            )

            if result.status == "failed" and not stage.allow_failure:
                run.status = "failed"
                run.logs.append(
                    f"[{run.id}] Stage '{stage.name}' failed and allow_failure=False."
                )
                return run

        if run.status != "failed" and run.status != "cancelled":
            run.status = "success"

        return run

    def _run_parallel(
        self, pipeline: PipelineConfig, env: Dict[str, str], run: PipelineRun
    ) -> PipelineRun:
        run.status = "running"
        run.logs.append(f"[{run.id}] Pipeline '{pipeline.name}' started (parallel).")

        stage_map = self._resolve_stages(pipeline, env)
        results: List[StageResult] = []
        any_failed = False

        for stage_name in pipeline.stages:
            if run.id in self._cancelled:
                run.status = "cancelled"
                run.logs.append(f"[{run.id}] Pipeline cancelled.")
                return run

            stage = stage_map.get(stage_name)
            if stage is None:
                continue

            result = self.run_stage(stage, env)
            results.append(result)
            run.logs.append(
                f"[{run.id}] Stage '{stage.name}' -> {result.status} "
                f"(exit={result.exit_code}, {result.duration:.2f}s)"
            )

            if result.status == "failed" and not stage.allow_failure:
                any_failed = True

        run.stage_results = results

        if run.id in self._cancelled:
            run.status = "cancelled"
        elif any_failed:
            run.status = "failed"
        else:
            run.status = "success"

        return run

    def _resolve_stages(
        self, pipeline: PipelineConfig, env: Dict[str, str]
    ) -> Dict[str, PipelineStage]:
        stages: Dict[str, PipelineStage] = {}
        for s in pipeline.stages:
            stage_env = dict(env)
            stages[s] = PipelineStage(name=s, env=stage_env)
        return stages

    def run_stage(
        self, stage: PipelineStage, env: Dict[str, str]
    ) -> StageResult:
        import subprocess

        started = time.time()
        merged_env = dict(env)
        merged_env.update(stage.env)

        if not stage.commands:
            return StageResult(
                name=stage.name,
                status="success",
                output="",
                exit_code=0,
                started_at=started,
                duration=0.0,
            )

        try:
            result = subprocess.run(
                stage.commands,
                capture_output=True,
                text=True,
                timeout=stage.timeout,
                env=merged_env,
            )
            duration = time.time() - started
            output = result.stdout + result.stderr
            exit_code = result.returncode
            status = "success" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            duration = time.time() - started
            output = ""
            exit_code = -1
            status = "failed"
        except FileNotFoundError:
            duration = time.time() - started
            output = "Command not found"
            exit_code = -1
            status = "failed"

        return StageResult(
            name=stage.name,
            status=status,
            output=output,
            exit_code=exit_code,
            started_at=started,
            duration=duration,
        )

    def cancel(self, run_id: str) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        self._cancelled.add(run_id)
        run.status = "cancelled"
        run.finished_at = time.time()
        run.logs.append(f"[{run_id}] Pipeline cancelled by user.")

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        return self._runs.get(run_id)

    def list_runs(self) -> List[PipelineRun]:
        return list(self._runs.values())

    def get_logs(self, run_id: str) -> List[str]:
        run = self._runs.get(run_id)
        if run is None:
            return []
        return list(run.logs)

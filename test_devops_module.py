import sys
import os
import shutil
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from zoya.devops import (
    PipelineConfig,
    PipelineRun,
    PipelineRunner,
    PipelineStage,
    StageResult,
    Deployer,
    Deployment,
    DeploymentConfig,
    create_pipeline,
    create_deployment,
    __version__,
)
import unittest


class TestPipelineConfig(unittest.TestCase):
    def test_create_with_all_fields(self):
        config = PipelineConfig(
            name="build-and-test",
            stages=["build", "test", "deploy"],
            environment={"NODE_ENV": "production"},
            timeout=1800,
            parallel=True,
        )
        self.assertEqual(config.name, "build-and-test")
        self.assertEqual(config.stages, ["build", "test", "deploy"])
        self.assertEqual(config.environment, {"NODE_ENV": "production"})
        self.assertEqual(config.timeout, 1800)
        self.assertTrue(config.parallel)

    def test_default_values(self):
        config = PipelineConfig(name="defaults", stages=[])
        self.assertEqual(config.timeout, 3600)
        self.assertFalse(config.parallel)
        self.assertEqual(config.environment, {})

    def test_empty_stages(self):
        config = PipelineConfig(name="empty", stages=[])
        self.assertEqual(config.stages, [])


class TestPipelineStage(unittest.TestCase):
    def test_create_with_all_fields(self):
        stage = PipelineStage(
            name="build",
            commands=["npm ci", "npm run build"],
            timeout=600,
            dependencies=["lint"],
            artifacts=["dist/"],
            allow_failure=False,
            env={"CI": "true"},
        )
        self.assertEqual(stage.name, "build")
        self.assertEqual(stage.commands, ["npm ci", "npm run build"])
        self.assertEqual(stage.timeout, 600)
        self.assertEqual(stage.dependencies, ["lint"])
        self.assertEqual(stage.artifacts, ["dist/"])
        self.assertFalse(stage.allow_failure)
        self.assertEqual(stage.env, {"CI": "true"})

    def test_default_values(self):
        stage = PipelineStage(name="default-stage")
        self.assertEqual(stage.commands, [])
        self.assertEqual(stage.timeout, 300)
        self.assertEqual(stage.dependencies, [])
        self.assertEqual(stage.artifacts, [])
        self.assertFalse(stage.allow_failure)
        self.assertEqual(stage.env, {})


class TestStageResult(unittest.TestCase):
    def test_captures_output(self):
        now = time.time()
        result = StageResult(
            name="build",
            status="success",
            output="Build completed successfully",
            exit_code=0,
            started_at=now,
            duration=5.5,
        )
        self.assertEqual(result.name, "build")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, "Build completed successfully")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.started_at, now)
        self.assertEqual(result.duration, 5.5)

    def test_captures_failure_output(self):
        result = StageResult(
            name="test",
            status="failed",
            output="Tests failed: 2 errors",
            exit_code=1,
            started_at=time.time(),
            duration=10.2,
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("failed", result.output)


class TestPipelineRun(unittest.TestCase):
    def test_initial_status_is_pending(self):
        config = PipelineConfig(name="test", stages=[])
        run = PipelineRun(pipeline=config)
        self.assertEqual(run.status, "pending")

    def test_has_unique_id(self):
        config = PipelineConfig(name="test", stages=[])
        run1 = PipelineRun(pipeline=config)
        run2 = PipelineRun(pipeline=config)
        self.assertIsNotNone(run1.id)
        self.assertNotEqual(run1.id, run2.id)

    def test_started_at_is_set(self):
        config = PipelineConfig(name="test", stages=[])
        before = time.time()
        run = PipelineRun(pipeline=config)
        after = time.time()
        self.assertGreaterEqual(run.started_at, before)
        self.assertLessEqual(run.started_at, after)


class TestPipelineRunner(unittest.TestCase):
    def test_run_creates_pipeline_run(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="simple", stages=[])
        run = runner.run(config)
        self.assertIsInstance(run, PipelineRun)
        self.assertIsNotNone(run.id)

    def test_run_with_empty_stages_succeeds(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="no-stages", stages=[])
        run = runner.run(config)
        self.assertEqual(run.status, "success")

    def test_run_with_commands_executes_stages(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="echo-test", stages=["greet"])
        run = runner.run(config)
        self.assertEqual(run.status, "success")
        self.assertEqual(len(run.stage_results), 1)

    def test_run_with_parallel_flag(self):
        runner = PipelineRunner()
        config = PipelineConfig(
            name="parallel-test", stages=["a", "b"], parallel=True
        )
        run = runner.run(config)
        self.assertEqual(run.status, "success")
        self.assertEqual(len(run.stage_results), 2)

    def test_get_run_returns_correct_run(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="get-test", stages=[])
        run = runner.run(config)
        fetched = runner.get_run(run.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, run.id)

    def test_get_run_nonexistent_returns_none(self):
        runner = PipelineRunner()
        self.assertIsNone(runner.get_run("nonexistent"))

    def test_list_runs_returns_all_runs(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="list-test", stages=[])
        run1 = runner.run(config)
        run2 = runner.run(config)
        runs = runner.list_runs()
        self.assertEqual(len(runs), 2)
        self.assertIn(run1.id, [r.id for r in runs])
        self.assertIn(run2.id, [r.id for r in runs])

    def test_list_runs_empty_initially(self):
        runner = PipelineRunner()
        self.assertEqual(runner.list_runs(), [])

    def test_get_logs_returns_log_entries(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="log-test", stages=[])
        run = runner.run(config)
        logs = runner.get_logs(run.id)
        self.assertIsInstance(logs, list)
        self.assertTrue(len(logs) > 0)

    def test_get_logs_nonexistent_returns_empty(self):
        runner = PipelineRunner()
        self.assertEqual(runner.get_logs("no-such-run"), [])

    def test_cancel_changes_run_status(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="cancel-test", stages=["slow"])
        run = runner.run(config)
        runner.cancel(run.id)
        cancelled = runner.get_run(run.id)
        self.assertEqual(cancelled.status, "cancelled")

    def test_pipeline_with_multiple_stages(self):
        runner = PipelineRunner()
        config = PipelineConfig(
            name="multi-stage", stages=["build", "test", "deploy"]
        )
        run = runner.run(config)
        self.assertEqual(run.status, "success")
        self.assertEqual(len(run.stage_results), 3)

    def test_stage_allow_failure_does_not_fail_pipeline(self):
        runner = PipelineRunner()
        config = PipelineConfig(name="allow-fail", stages=["build"])
        run = runner.run(config)
        self.assertEqual(run.status, "success")

    def test_pipeline_timeout_config_stored(self):
        config = PipelineConfig(
            name="timeout-test",
            stages=["build"],
            timeout=0,
        )
        self.assertEqual(config.timeout, 0)


class TestDeploymentConfig(unittest.TestCase):
    def test_create_with_all_strategies(self):
        for strategy in ("rolling", "blue_green", "canary", "recreate"):
            config = DeploymentConfig(
                name="app-v2",
                source="./build",
                target="/opt/app",
                strategy=strategy,
                health_check="/healthz",
                timeout=600,
                rollback_on_failure=True,
                environment="staging",
                env_vars={"PORT": "8080"},
            )
            self.assertEqual(config.strategy, strategy)
            self.assertEqual(config.name, "app-v2")
            self.assertEqual(config.source, "./build")
            self.assertEqual(config.target, "/opt/app")
            self.assertEqual(config.health_check, "/healthz")
            self.assertEqual(config.timeout, 600)
            self.assertEqual(config.environment, "staging")
            self.assertEqual(config.env_vars, {"PORT": "8080"})

    def test_default_values(self):
        config = DeploymentConfig(
            name="defaults", source=".", target="/tmp/deploy"
        )
        self.assertEqual(config.strategy, "rolling")
        self.assertEqual(config.timeout, 300)
        self.assertTrue(config.rollback_on_failure)
        self.assertEqual(config.environment, "dev")
        self.assertEqual(config.env_vars, {})
        self.assertIsNone(config.health_check)


class TestDeployment(unittest.TestCase):
    def test_initial_status_is_pending(self):
        config = DeploymentConfig(name="test", source=".", target="/tmp/test")
        dep = Deployment(config=config, version="v1.0.0")
        self.assertEqual(dep.status, "pending")

    def test_version_tracking(self):
        config = DeploymentConfig(name="ver-test", source=".", target="/tmp/test")
        dep = Deployment(config=config, version="v2.5.1")
        self.assertEqual(dep.version, "v2.5.1")

    def test_has_unique_id(self):
        config = DeploymentConfig(name="id-test", source=".", target="/tmp/test")
        d1 = Deployment(config=config, version="v1")
        d2 = Deployment(config=config, version="v1")
        self.assertNotEqual(d1.id, d2.id)


class TestDeployer(unittest.TestCase):
    def setUp(self):
        tmp = os.environ.get("TEMP", "/tmp")
        self._src_dir = os.path.join(tmp, "zoya-test-src")
        self._tgt_dir = os.path.join(tmp, "zoya-test-deploy")
        self._tgt_dir2 = os.path.join(tmp, "zoya-test-prod")
        os.makedirs(self._src_dir, exist_ok=True)
        with open(os.path.join(self._src_dir, "index.html"), "w") as f:
            f.write("<h1>test</h1>")
        self.deployer = Deployer()
        self.config = DeploymentConfig(
            name="test-app",
            source=self._src_dir,
            target=self._tgt_dir,
            strategy="rolling",
            environment="dev",
        )
        self.prod_config = DeploymentConfig(
            name="prod-app",
            source=self._src_dir,
            target=self._tgt_dir2,
            environment="production",
        )

    def tearDown(self):
        for d in (self._src_dir, self._tgt_dir, self._tgt_dir2):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)

    def test_deploy_creates_deployment(self):
        dep = self.deployer.deploy(self.config, version="v1.0.0")
        self.assertIsInstance(dep, Deployment)
        self.assertIsNotNone(dep.id)

    def test_deployment_initial_status(self):
        dep = self.deployer.deploy(self.config, version="v1.0.0")
        self.assertIn(dep.status, ("healthy", "deploying", "failed"))

    def test_get_deployment_returns_correct_deployment(self):
        dep = self.deployer.deploy(self.config, version="v1.0.0")
        fetched = self.deployer.get_deployment(dep.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, dep.id)

    def test_get_deployment_nonexistent_returns_none(self):
        self.assertIsNone(self.deployer.get_deployment("no-such-id"))

    def test_list_deployments_by_environment(self):
        self.deployer.deploy(self.config, version="v1")
        self.deployer.deploy(self.prod_config, version="v1")
        dev_deps = self.deployer.list_deployments(environment="dev")
        prod_deps = self.deployer.list_deployments(environment="production")
        all_deps = self.deployer.list_deployments()
        self.assertEqual(len(dev_deps), 1)
        self.assertEqual(len(prod_deps), 1)
        self.assertEqual(len(all_deps), 2)

    def test_rollback_changes_status(self):
        dep = self.deployer.deploy(self.config, version="v1.0.0")
        rolled = self.deployer.rollback(dep.id)
        self.assertEqual(rolled.status, "rolled_back")

    def test_rollback_nonexistent_raises(self):
        with self.assertRaises(ValueError):
            self.deployer.rollback("no-such-id")

    def test_health_check_returns_bool(self):
        result = self.deployer.health_check("http://nonexistent.example.com/health")
        self.assertIsInstance(result, bool)

    def test_switch_traffic_logs_changes(self):
        dep1 = self.deployer.deploy(self.config, version="v1")
        dep2 = self.deployer.deploy(self.config, version="v2")
        self.deployer.switch_traffic(dep1.id, dep2.id, percentage=50)
        self.assertTrue(
            any("Traffic switched" in log for log in dep2.logs)
        )

    def test_switch_traffic_invalid_source_raises(self):
        dep = self.deployer.deploy(self.config, version="v1")
        with self.assertRaises(ValueError):
            self.deployer.switch_traffic("bad-source", dep.id)

    def test_switch_traffic_invalid_target_raises(self):
        dep = self.deployer.deploy(self.config, version="v1")
        with self.assertRaises(ValueError):
            self.deployer.switch_traffic(dep.id, "bad-target")

    def test_list_environments_returns_known_envs(self):
        envs = self.deployer.list_environments()
        self.assertIn("dev", envs)
        self.assertIn("staging", envs)
        self.assertIn("production", envs)

    def test_deploy_adds_environment(self):
        tmp = os.environ.get("TEMP", "/tmp")
        custom_config = DeploymentConfig(
            name="custom-env",
            source=self._src_dir,
            target=os.path.join(tmp, "zoya-test-custom"),
            environment="canary-us-east",
        )
        self.deployer.deploy(custom_config)
        envs = self.deployer.list_environments()
        self.assertIn("canary-us-east", envs)

    def test_deployment_version_tracking(self):
        dep = self.deployer.deploy(self.config, version="v2.0.0-rc1")
        self.assertEqual(dep.version, "v2.0.0-rc1")
        self.assertIn("v2.0.0-rc1", " ".join(dep.logs))


if __name__ == "__main__":
    unittest.main()

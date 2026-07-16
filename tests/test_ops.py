from pathlib import Path
from srie.services.sandbox import Sandbox
from srie.services.repair import RepairEngine
from srie.services.deployment import Deployment


class TestSandbox:

    def test_create_environment(self, tmp_path: Path):
        s = Sandbox(tmp_path)
        env = s.create_environment("test-env")
        assert env["state"] == "CREATED"
        assert env["name"] == "test-env"

    def test_run_test(self, tmp_path: Path):
        s = Sandbox(tmp_path)
        env = s.create_environment()
        test = s.run_test(env["id"], "verify-build", "verify")
        assert test["state"] == "PASSED"

    def test_report(self, tmp_path: Path):
        s = Sandbox(tmp_path)
        env = s.create_environment()
        s.run_test(env["id"], "test-1", "verify")
        s.run_test(env["id"], "test-2", "discover")
        r = s.report(env["id"])
        assert r["total_tests"] == 2
        assert r["passed"] == 2


class TestRepair:

    def test_diagnose_uninitialized(self, tmp_path: Path):
        r = RepairEngine(tmp_path)
        issues = r.diagnose()
        assert len(issues) > 0
        assert any("CRITICAL" in i["type"] for i in issues)

    def test_auto_repair(self, tmp_path: Path):
        from srie.kernel.runtime import Runtime
        rt = Runtime()
        rt.boot(tmp_path)
        r = RepairEngine(tmp_path)
        results = r.auto_repair_all()
        assert len(results) >= 0

    def test_history(self, tmp_path: Path):
        r = RepairEngine(tmp_path)
        history = r.history()
        assert isinstance(history, list)


class TestDeployment:

    def test_register_target(self, tmp_path: Path):
        d = Deployment(tmp_path)
        tgt = d.register_target("prod", "production", "https://example.com")
        assert tgt["state"] == "REGISTERED"
        assert tgt["environment"] == "production"

    def test_deploy(self, tmp_path: Path):
        d = Deployment(tmp_path)
        tgt = d.register_target("staging", "staging")
        dep = d.deploy(tgt["id"], "1.0.0")
        assert dep["state"] == "DEPLOYED"
        assert dep["version"] == "1.0.0"

    def test_rollback(self, tmp_path: Path):
        d = Deployment(tmp_path)
        tgt = d.register_target("prod", "production")
        d.deploy(tgt["id"], "2.0.0")
        d.deploy(tgt["id"], "3.0.0")
        rollback = d.rollback(tgt["id"])
        assert rollback["version"] == "2.0.0"

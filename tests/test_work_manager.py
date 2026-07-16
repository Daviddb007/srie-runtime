from pathlib import Path
from srie.kernel.session import Session
from srie.kernel.activity import Activity
from srie.kernel.task import Task
from srie.kernel.workspace import Workspace
from srie.services.work_log import WorkLog


class TestSession:

    def test_start_and_end(self, tmp_path: Path):
        import time
        s = Session(tmp_path)
        session = s.start(user="david")
        assert session["state"] == "ACTIVE"
        assert session["user"] == "david"

        time.sleep(0.01)
        ended = s.end()
        assert ended["state"] == "COMPLETED"
        assert ended["duration_seconds"] >= 0

    def test_latest_active(self, tmp_path: Path):
        s = Session(tmp_path)
        s.start()
        current = s.current()
        assert current is not None
        assert current["state"] == "ACTIVE"


class TestActivity:

    def test_begin_and_complete(self, tmp_path: Path):
        a = Activity(tmp_path)
        act = a.begin("discovery", objective="Inventory project")
        assert act["state"] == "RUNNING"
        assert act["type"] == "discovery"

        completed = a.complete(hypotheses=14, confidence=0.87)
        assert completed["state"] == "COMPLETED"
        assert completed["reasoning"]["hypothesis_count"] == 14

    def test_reasoning_context(self, tmp_path: Path):
        a = Activity(tmp_path)
        a.begin("diagnosis", objective="Find issues")
        a.reasoning(
            hypothesis_count=10,
            confirmed=5,
            discarded=5,
            confidence=0.75,
            cost_usd=0.18,
            models=["GPT-5.5"],
        )
        current = a.current()
        assert current["reasoning"]["models"] == ["GPT-5.5"]
        assert current["reasoning"]["cost_usd"] == 0.18


class TestTask:

    def test_create_and_transition(self, tmp_path: Path):
        t = Task(tmp_path)
        task = t.create("Scan git", activity_id="act-001")
        assert task["state"] == "PENDING"
        assert task["name"] == "Scan git"

        running = t.transition(task["id"], "RUNNING")
        assert running["state"] == "RUNNING"

        completed = t.transition(task["id"], "COMPLETED")
        assert completed["state"] == "COMPLETED"

    def test_invalid_transition(self, tmp_path: Path):
        t = Task(tmp_path)
        task = t.create("Bad task")
        import pytest
        with pytest.raises(ValueError, match="Invalid transition"):
            t.transition(task["id"], "COMPLETED")  # PENDING -> not COMPLETED

    def test_resumable(self, tmp_path: Path):
        t = Task(tmp_path)
        task = t.create("Long task")
        t.transition(task["id"], "RUNNING")
        resumed = t.transition(task["id"], "RESUMABLE")
        assert resumed["state"] == "RESUMABLE"

    def test_blocked(self, tmp_path: Path):
        t = Task(tmp_path)
        task = t.create("Wait for resource")
        t.transition(task["id"], "RUNNING")
        blocked = t.transition(task["id"], "BLOCKED")
        assert blocked["state"] == "BLOCKED"
        unblocked = t.transition(task["id"], "RUNNING")
        assert unblocked["state"] == "RUNNING"


class TestWorkspace:

    def test_ensure_creates(self, tmp_path: Path):
        w = Workspace(tmp_path)
        data = w.ensure(name="Stonelytics", organization="SRIE Lab")
        assert data["workspace"]["name"] == "Stonelytics"
        assert data["workspace"]["state"] == "ACTIVE"

    def test_load_existing(self, tmp_path: Path):
        w = Workspace(tmp_path)
        w.ensure(name="Test")
        loaded = w.load()
        assert loaded["workspace"]["name"] == "Test"


class TestWorkLog:

    def test_consolidate(self, tmp_path: Path):
        wl = WorkLog(tmp_path)
        activities = [
            {"id": "act-001", "type": "discovery", "reasoning": {"hypothesis_count": 10, "confidence": 0.8}, "started": "2026-01-01T10:00:00", "ended": "2026-01-01T10:30:00"},
            {"id": "act-002", "type": "planning", "reasoning": {"hypothesis_count": 5, "confidence": 0.9}, "started": "2026-01-01T10:30:00", "ended": "2026-01-01T11:00:00"},
        ]
        dna = wl.consolidate("ses-001", activities)
        assert dna["activity_count"] == 2
        assert dna["type_distribution"]["discovery"] == 1

    def test_dna_summary(self, tmp_path: Path):
        wl = WorkLog(tmp_path)
        dna = wl.dna()
        assert dna["total_sessions"] == 0

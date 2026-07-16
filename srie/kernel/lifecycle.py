from __future__ import annotations
from enum import Enum


class RuntimeState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    FAILED = "FAILED"


VALID_TRANSITIONS = {
    RuntimeState.STOPPED: [RuntimeState.STARTING],
    RuntimeState.STARTING: [RuntimeState.RUNNING, RuntimeState.FAILED, RuntimeState.STOPPING],
    RuntimeState.RUNNING: [RuntimeState.PAUSED, RuntimeState.STOPPING, RuntimeState.FAILED],
    RuntimeState.PAUSED: [RuntimeState.RUNNING, RuntimeState.STOPPING],
    RuntimeState.STOPPING: [RuntimeState.STOPPED, RuntimeState.FAILED],
    RuntimeState.FAILED: [RuntimeState.STOPPED],
}


class Lifecycle:

    def __init__(self):
        self._state = RuntimeState.STOPPED

    @property
    def state(self) -> RuntimeState:
        return self._state

    def transition(self, target: RuntimeState) -> None:
        if target in VALID_TRANSITIONS.get(self._state, []):
            self._state = target
        else:
            raise ValueError(f"Invalid transition: {self._state.value} -> {target.value}")

    def reset(self) -> None:
        self._state = RuntimeState.STOPPED

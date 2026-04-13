"""
Execution trace recording for mock backend.

Records and serializes the execution trace from mock backend operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


@dataclass(frozen=True)
class ExecutionStep:
    """
    A single step in the execution trace.

    Attributes:
        step_id: Unique identifier for the step
        operation: The backend operation name
        inputs: Input parameters for the operation
        outputs: Output metrics from the operation
        status: Execution status
        duration_ms: Operation duration in milliseconds
        timestamp: When the step started (ms since epoch)
    """
    step_id: str
    operation: str
    inputs: dict
    outputs: dict
    status: str
    duration_ms: float
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "operation": self.operation,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }


@dataclass(frozen=True)
class ExecutionTrace:
    """
    Complete execution trace for a scenario.

    Attributes:
        scenario_name: Name of the scenario
        steps: Ordered list of execution steps
        start_time: When execution started
        end_time: When execution ended
        total_duration_ms: Total execution duration
    """
    scenario_name: str
    steps: tuple[ExecutionStep, ...]
    start_time: float
    end_time: float
    total_duration_ms: float

    def to_dict(self) -> dict:
        return {
            "scenario_name": self.scenario_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "steps": [s.to_dict() for s in self.steps]
        }


class ExecutionTracer:
    """
    Traces execution of mock backend operations.

    Records all operations with timestamps and outputs for later analysis.
    """

    def __init__(self, scenario_name: str):
        """Initialize the tracer for a scenario."""
        self.scenario_name = scenario_name
        self.steps: List[ExecutionStep] = []
        self.start_time = 0.0
        self.end_time = 0.0
        self._step_counter = 0

    def start(self):
        """Start tracing."""
        self.start_time = self._get_timestamp()

    def end(self):
        """End tracing."""
        self.end_time = self._get_timestamp()

    def record(self, operation: str, inputs: dict, outputs: dict, status: str, duration_ms: float):
        """Record an execution step."""
        self._step_counter += 1
        step = ExecutionStep(
            step_id=f"step_{self._step_counter:04d}",
            operation=operation,
            inputs=inputs,
            outputs=outputs,
            status=status,
            duration_ms=duration_ms,
            timestamp=self._get_timestamp()
        )
        self.steps.append(step)

    def _get_timestamp(self) -> float:
        """Get current timestamp in milliseconds."""
        import time
        return time.time() * 1000

    def to_trace(self) -> ExecutionTrace:
        """Create an ExecutionTrace from captured steps."""
        return ExecutionTrace(
            scenario_name=self.scenario_name,
            steps=tuple(self.steps),
            start_time=self.start_time,
            end_time=self.end_time,
            total_duration_ms=self.end_time - self.start_time if self.end_time else 0
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        trace = self.to_trace()
        return trace.to_dict()

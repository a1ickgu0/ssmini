"""
Lowering module for OSC DSL compiler.

Transforms Semantic IR to Execution IR and provides backend execution.
"""

from compiler.lowering.mock_backend import MockBackend, OperationResult, OperationStatus
from compiler.lowering.execution_trace import ExecutionTracer, ExecutionTrace
from compiler.lowering.e2e_pipeline import (
    ValidationStatus,
    ValidationIssue,
    ExecutionMetrics,
    ExecutionResult,
    E2EPipelineResult,
)

__all__ = [
    "MockBackend",
    "OperationResult",
    "OperationStatus",
    "ExecutionTracer",
    "ExecutionTrace",
    "ValidationStatus",
    "ValidationIssue",
    "ExecutionMetrics",
    "ExecutionResult",
    "E2EPipelineResult",
]

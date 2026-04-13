"""
Action binding module for OSC DSL compiler.

This module provides:
- BindingEntry: Dataclass for binding configuration
- BindingLoader: Load binding.yaml configurations
- ExecutionPlanMapper: Map semantic IR to backend operations
"""

from compiler.bindings.loader import BindingEntry, BindingLoader
from compiler.bindings.mapper import (
    ExecutionMode,
    MappedAction,
    MappedPhase,
    MappedExecutionPlan,
    ExecutionPlanMapper,
)

__all__ = [
    "BindingEntry",
    "BindingLoader",
    "ExecutionMode",
    "MappedAction",
    "MappedPhase",
    "MappedExecutionPlan",
    "ExecutionPlanMapper",
]

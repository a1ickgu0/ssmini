"""
Runtime module for OSC DSL compiler.

This module provides runtime validation capabilities:
- Constraint validation (equality, range, presence)
- Checker spec generation
- Execution result checking
"""

from compiler.runtime.checker_spec import (
    ConstraintSpec,
    ConstraintType,
    ComparisonOperator,
    ValidationResult,
    CheckResult,
)
from compiler.runtime.validator import ConstraintValidator
from compiler.runtime.compile_checker_spec import compile_to_checker_spec

__all__ = [
    "ConstraintSpec",
    "ConstraintType",
    "ComparisonOperator",
    "ValidationResult",
    "CheckResult",
    "ConstraintValidator",
    "compile_to_checker_spec",
]

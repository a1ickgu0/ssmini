"""
Runtime constraint validator for OSC DSL compiler.

Validates execution results against constraint specifications.
"""

from typing import Union

from compiler.runtime.checker_spec import (
    ConstraintSpec,
    ConstraintType,
    ComparisonOperator,
    ValidationResult,
    CheckResult,
)


class ConstraintValidator:
    """
    Validates a single metric value against a constraint specification.
    """

    @staticmethod
    def validate_value(
        actual_value: Union[str, int, float, None],
        constraint: ConstraintSpec
    ) -> ValidationResult:
        """
        Validate an actual metric value against a constraint spec.

        Args:
            actual_value: The measured/observed metric value
            constraint: The constraint specification to check against

        Returns:
            ValidationResult indicating pass/fail and details
        """
        metric = constraint.metric

        # Check for missing required metric
        if actual_value is None:
            if constraint.required:
                return ValidationResult(
                    metric=metric,
                    passed=False,
                    actual_value=None,
                    expected_value=constraint.value,
                    reason=f"Missing required metric: {metric}"
                )
            else:
                # Optional metric missing - this is OK
                return ValidationResult(
                    metric=metric,
                    passed=True,
                    actual_value=None,
                    expected_value=None,
                    reason=f"Optional metric {metric} not present (OK)"
                )

        # Type-specific validation
        constraint_type = constraint.constraint_type

        if constraint_type == ConstraintType.PRESENCE:
            # Just check if value exists (not None)
            return ValidationResult(
                metric=metric,
                passed=actual_value is not None,
                actual_value=actual_value,
                expected_value=True,
                reason=f"Presence check: {'OK' if actual_value is not None else 'Missing'}"
            )

        elif constraint_type == ConstraintType.EQUALITY:
            return ConstraintValidator._validate_equality(
                metric, actual_value, constraint
            )

        elif constraint_type == ConstraintType.RANGE:
            return ConstraintValidator._validate_range(
                metric, actual_value, constraint
            )

        elif constraint_type == ConstraintType.RANGE_EXCLUSIVE:
            return ConstraintValidator._validate_rangeExclusive(
                metric, actual_value, constraint
            )

        else:
            return ValidationResult(
                metric=metric,
                passed=False,
                actual_value=actual_value,
                expected_value=constraint.value,
                reason=f"Unknown constraint type: {constraint_type}"
            )

    @staticmethod
    def _normalize_value(value: Union[int, float, str, bool, None]) -> Union[int, float, str, bool, None]:
        """Normalize a value for comparison."""
        if value is None:
            return None
        # Handle string representations of booleans and numbers
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            # Try to parse as number
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value
        return value

    @staticmethod
    def _validate_equality(
        metric: str,
        actual_value: Union[int, float, str, bool],
        constraint: ConstraintSpec
    ) -> ValidationResult:
        """Validate equality constraint."""
        expected = constraint.value

        # Normalize both values for comparison
        actual_normalized = ConstraintValidator._normalize_value(actual_value)
        expected_normalized = ConstraintValidator._normalize_value(expected)

        if constraint.operator == ComparisonOperator.EQUALS:
            passed = actual_normalized == expected_normalized
            reason = f"Equality check: {actual_value} == {expected}"
        elif constraint.operator == ComparisonOperator.NOT_EQUALS:
            passed = actual_normalized != expected_normalized
            reason = f"Inequality check: {actual_value} != {expected}"
        elif constraint.operator == ComparisonOperator.LESS_THAN:
            passed = actual_normalized < expected_normalized
            reason = f"Comparison: {actual_value} < {expected}"
        elif constraint.operator == ComparisonOperator.LESS_THAN_EQ:
            passed = actual_normalized <= expected_normalized
            reason = f"Comparison: {actual_value} <= {expected}"
        elif constraint.operator == ComparisonOperator.GREATER_THAN:
            passed = actual_normalized > expected_normalized
            reason = f"Comparison: {actual_value} > {expected}"
        elif constraint.operator == ComparisonOperator.GREATER_THAN_EQ:
            passed = actual_normalized >= expected_normalized
            reason = f"Comparison: {actual_value} >= {expected}"
        else:
            return ValidationResult(
                metric=metric,
                passed=False,
                actual_value=actual_value,
                expected_value=expected,
                reason=f"Unknown operator: {constraint.operator}"
            )

        return ValidationResult(
            metric=metric,
            passed=passed,
            actual_value=actual_value,
            expected_value=expected,
            reason=reason
        )

    @staticmethod
    def _validate_range(
        metric: str,
        actual_value: Union[int, float],
        constraint: ConstraintSpec
    ) -> ValidationResult:
        """Validate inclusive range constraint [start, end]."""
        if not isinstance(constraint.value, dict):
            return ValidationResult(
                metric=metric,
                passed=False,
                actual_value=actual_value,
                expected_value=constraint.value,
                reason="Range constraint requires a dict value with 'start' and 'end'"
            )

        range_spec = constraint.value
        start = range_spec.get("start")
        end = range_spec.get("end")
        inclusive = range_spec.get("inclusive", True)

        if start is None or end is None:
            return ValidationResult(
                metric=metric,
                passed=False,
                actual_value=actual_value,
                expected_value=constraint.value,
                reason="Range spec must have 'start' and 'end' values"
            )

        if inclusive:
            passed = start <= actual_value <= end
            reason = f"Range check: {start} <= {actual_value} <= {end}"
        else:
            passed = start < actual_value < end
            reason = f"Exclusive range check: {start} < {actual_value} < {end}"

        return ValidationResult(
            metric=metric,
            passed=passed,
            actual_value=actual_value,
            expected_value=constraint.value,
            reason=reason
        )

    @staticmethod
    def _validate_rangeExclusive(
        metric: str,
        actual_value: Union[int, float],
        constraint: ConstraintSpec
    ) -> ValidationResult:
        """Validate exclusive range constraint (start, end)."""
        # Reuse range validation with exclusive flag
        constraint = ConstraintSpec(
            metric=constraint.metric,
            constraint_type=ConstraintType.RANGE,
            operator=constraint.operator,
            value={
                "start": constraint.value.get("start"),
                "end": constraint.value.get("end"),
                "inclusive": False
            },
            anchor=constraint.anchor,
            required=constraint.required
        )
        return ConstraintValidator._validate_range(metric, actual_value, constraint)

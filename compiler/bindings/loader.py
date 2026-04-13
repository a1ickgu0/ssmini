"""
Binding loader for OSC DSL compiler.

Loads and parses binding.yaml configuration to map DSL actions
to backend operations.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path


@dataclass(frozen=True)
class BindingEntry:
    """
    Represents a single binding entry mapping a DSL action to a backend operation.

    Attributes:
        dsl_action: The DSL action name (e.g., "laptop.scan_ssid")
        backend_operation: The backend operation name (e.g., "wifi.scan")
        inputs: List of input parameters for the action
        outputs: List of output metrics produced by the action
    """
    dsl_action: str
    backend_operation: str
    inputs: tuple[str, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "dsl_action": self.dsl_action,
            "backend_operation": self.backend_operation,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BindingEntry":
        return cls(
            dsl_action=data["dsl_action"],
            backend_operation=data["backend_operation"],
            inputs=tuple(data.get("inputs", [])),
            outputs=tuple(data.get("outputs", []))
        )


class SimpleYamlParser:
    """
    Simple YAML parser for binding files.
    Handles the specific structure of binding.yaml format.
    """

    @classmethod
    def parse(cls, content: str) -> dict:
        """Parse YAML content into a dictionary."""
        result = {}
        lines = content.split('\n')
        current_key = None
        current_data = {}

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue

            # Calculate indentation
            indent = cls._get_indent(line)

            # Top-level key (no indent or indent < 2)
            if indent < 2 and ':' in stripped:
                # Save previous entry if exists
                if current_key is not None:
                    result[current_key] = current_data
                    current_data = {}

                current_key = stripped.split(':')[0].strip()
                # Check if value is on same line (e.g., key: value)
                value_part = stripped.split(':', 1)[1].strip() if ':' in stripped else ''
                if value_part:
                    # Inline value
                    if value_part == '[]':
                        current_data['inputs'] = []
                        current_data['outputs'] = []
                    elif value_part == '{}':
                        current_data['inputs'] = {}
                        current_data['outputs'] = {}

            # Nested fields (indent >= 2)
            elif indent >= 2 and current_key is not None:
                if ':' in stripped:
                    key, value = stripped.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == 'backend':
                        current_data['backend'] = value
                    elif key == 'inputs':
                        current_data['inputs'] = cls._parse_list(value)
                    elif key == 'outputs':
                        current_data['outputs'] = cls._parse_list(value)

            i += 1

        # Save last entry
        if current_key is not None:
            result[current_key] = current_data

        return result

    @classmethod
    def _get_indent(cls, line: str) -> int:
        """Get indentation level (number of leading spaces)."""
        return len(line) - len(line.lstrip())

    @classmethod
    def _parse_list(cls, value: str) -> list[str]:
        """Parse a list like [a, b, c] or single item."""
        value = value.strip()
        if value == '[]':
            return []
        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            return [item.strip() for item in items if item.strip()]
        return [value]


class BindingLoader:
    """
    Loads binding configuration from YAML file.

    The binding file maps DSL action names to backend operations,
    allowing the compiler to decouple DSL from specific backends.
    """

    def __init__(self):
        self._bindings: Dict[str, BindingEntry] = {}
        self._reverse_bindings: Dict[str, str] = {}

    def load(self, path: str | Path) -> Dict[str, BindingEntry]:
        """
        Load bindings from a YAML file.

        Args:
            path: Path to the binding.yaml file

        Returns:
            Dictionary mapping DSL action names to BindingEntry objects
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Binding file not found: {path}")

        with open(path, 'r') as f:
            content = f.read()

        config = SimpleYamlParser.parse(content)

        self._bindings = {}
        self._reverse_bindings = {}

        if config:
            for dsl_action, binding_data in config.items():
                if binding_data is None:
                    binding_data = {}

                entry = BindingEntry(
                    dsl_action=dsl_action,
                    backend_operation=binding_data.get("backend", dsl_action),
                    inputs=tuple(binding_data.get("inputs", [])),
                    outputs=tuple(binding_data.get("outputs", []))
                )
                self._bindings[dsl_action] = entry
                self._reverse_bindings[binding_data.get("backend", dsl_action)] = dsl_action

        return self._bindings

    def get_binding(self, dsl_action: str) -> Optional[BindingEntry]:
        """
        Get the binding entry for a DSL action.

        Args:
            dsl_action: The DSL action name (e.g., "laptop.scan_ssid")

        Returns:
            BindingEntry if found, None otherwise
        """
        return self._bindings.get(dsl_action)

    def lookup_backend(self, dsl_action: str) -> Optional[str]:
        """
        Look up the backend operation for a DSL action.

        Args:
            dsl_action: The DSL action name

        Returns:
            Backend operation name or None if not found
        """
        entry = self._bindings.get(dsl_action)
        return entry.backend_operation if entry else None

    def lookup_dsl(self, backend_operation: str) -> Optional[str]:
        """
        Look up the DSL action for a backend operation.

        Args:
            backend_operation: The backend operation name

        Returns:
            DSL action name or None if not found
        """
        return self._reverse_bindings.get(backend_operation)

    def list_all_bindings(self) -> list[BindingEntry]:
        """Return all loaded binding entries."""
        return list(self._bindings.values())

    def has_binding(self, dsl_action: str) -> bool:
        """Check if a binding exists for the given DSL action."""
        return dsl_action in self._bindings

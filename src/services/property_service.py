import logging
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Iterable, Optional


class PropertyService:
    """
    A standalone, stateless service responsible for navigating and modifying
    the hierarchical property trees of domain objects using string paths.
    
    Supports:
    - Nested dataclasses, dictionaries, and lists.
    - Wildcard expansion (e.g., 'artists.*.visible').
    - Type-safe leaf setting (Enums, numeric conversion).
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_value(self, obj: Any, path: str) -> Any:
        """
        Navigates a concrete path and returns the value at the leaf.
        Raises AttributeError, KeyError, or IndexError if the path is invalid.
        """
        curr = obj
        for part in path.split("."):
            if isinstance(curr, dict):
                curr = curr[part]
            elif isinstance(curr, list):
                curr = curr[int(part)]
            else:
                curr = getattr(curr, part)
        return curr

    def set_value(self, obj: Any, path: str, value: Any):
        """
        Navigates to the parent of the leaf attribute and sets the new value.
        Handles basic type coercion for common UI inputs.
        """
        parts = path.split(".")
        target = obj
        
        # 1. Navigate to the parent of the leaf
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target[part]
            elif isinstance(target, list):
                target = target[int(part)]
            else:
                target = getattr(target, part)

        leaf_name = parts[-1]
        
        # 2. Extract type info for coercion if it's a dataclass field
        target_type = None
        if is_dataclass(target):
            field_map = {f.name: f.type for f in fields(target)}
            if leaf_name in field_map:
                target_type = field_map[leaf_name]

        # 3. Apply value with coercion
        final_value = self._coerce_value(value, target_type)
        
        if isinstance(target, dict):
            target[leaf_name] = final_value
        elif isinstance(target, list):
            target[int(leaf_name)] = final_value
        else:
            setattr(target, leaf_name, final_value)

    def resolve_concrete_paths(self, obj: Any, path: str) -> list[str]:
        """Expands wildcards into concrete paths."""
        parts = path.split(".")
        return list(self._recursive_resolve(obj, parts, ""))

    def _recursive_resolve(self, obj: Any, parts: list[str], current_path: str) -> Iterable[str]:
        if not parts:
            yield current_path.strip(".")
            return

        part = parts[0]
        remaining = parts[1:]

        if part == "*":
            if isinstance(obj, dict):
                for key in obj.keys():
                    yield from self._recursive_resolve(
                        obj[key], remaining, f"{current_path}.{key}"
                    )
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    yield from self._recursive_resolve(
                        obj[i], remaining, f"{current_path}.{i}"
                    )
        else:
            try:
                if isinstance(obj, dict) and part in obj:
                    yield from self._recursive_resolve(
                        obj[part], remaining, f"{current_path}.{part}"
                    )
                elif isinstance(obj, list):
                    idx = int(part)
                    if 0 <= idx < len(obj):
                        yield from self._recursive_resolve(
                            obj[idx], remaining, f"{current_path}.{part}"
                        )
                elif hasattr(obj, part):
                    yield from self._recursive_resolve(
                        getattr(obj, part), remaining, f"{current_path}.{part}"
                    )
            except (ValueError, TypeError):
                pass

    def _coerce_value(self, value: Any, target_type: Optional[Any]) -> Any:
        """Helper to convert raw input (often strings from UI) to the expected type."""
        if target_type is None or value is None:
            return value

        # Handle Enums
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            if isinstance(value, str):
                try:
                    return target_type(value)
                except ValueError:
                    return value
            return value

        # Handle numeric conversion for strings from UI
        if isinstance(value, str):
            try:
                if target_type is float:
                    return float(value)
                if target_type is int:
                    return int(value)
            except ValueError:
                pass

        return value

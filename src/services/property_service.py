import logging
from dataclasses import fields, is_dataclass, replace
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
        Sets a value at a path. If an intermediate parent is a frozen dataclass,
        it performs a replacement higher up the chain.
        """
        parts = path.split(".")
        
        # Base case: single attribute
        if len(parts) == 1:
            self._set_direct_value(obj, parts[0], value)
            return

        # Recursive case: navigate and replace if needed
        parent_path = ".".join(parts[:-1])
        leaf_name = parts[-1]
        
        parent = self.get_value(obj, parent_path)
        
        try:
            self._set_direct_value(parent, leaf_name, value)
        except Exception:
            # If direct set fails (e.g. FrozenInstanceError), we must replace the parent 
            # object on ITS parent.
            if is_dataclass(parent):
                
                # 1. Coerce value for the leaf
                field_map = {f.name: f.type for f in fields(parent)}
                target_type = field_map.get(leaf_name)
                final_value = self._coerce_value(value, target_type)
                
                # 2. Create new parent instance
                new_parent = replace(parent, **{leaf_name: final_value})
                
                # 3. Recursively set the new parent on the original object
                self.set_value(obj, parent_path, new_parent)
            else:
                raise

    def _set_direct_value(self, target: Any, attr: str, value: Any):
        """Applies value with coercion to a direct attribute/key/index."""
        target_type = None
        if is_dataclass(target):
            field_map = {f.name: f.type for f in fields(target)}
            target_type = field_map.get(attr)

        final_value = self._coerce_value(value, target_type)

        if isinstance(target, dict):
            target[attr] = final_value
        elif isinstance(target, list):
            target[int(attr)] = final_value
        else:
            setattr(target, attr, final_value)

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

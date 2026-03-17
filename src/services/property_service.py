import logging
from dataclasses import fields, is_dataclass, replace
from enum import Enum
from typing import Any, Iterable, Optional, Union, get_origin, get_args

from src.models.nodes.scene_node import SceneNode
from src.shared.color import Color
from src.shared.units import Dimension, Unit
from src.shared.primitives import Alpha, ZOrder


class PropertyService:
    """
    A standalone, stateless service responsible for navigating and modifying
    the hierarchical property trees of domain objects using string paths.
    
    Supports:
    - Nested dataclasses, dictionaries, and lists.
    - Functional, immutable updates for frozen dataclasses.
    - Wildcard expansion (e.g., 'artists.*.visuals.color').
    - Primitive Projection for UI integration.
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

    def get_projected_value(self, obj: Any, path: str) -> Any:
        """
        Navigates to the leaf and 'unwraps' Value Objects for UI consumption.
        (e.g., Dimension -> float, Color -> hex string).
        """
        val = self.get_value(obj, path)
        
        if isinstance(val, Dimension):
            return val.value
        if isinstance(val, Color):
            return val.to_hex()
        if isinstance(val, Alpha):
            return float(val)
        if isinstance(val, ZOrder):
            return int(val)
            
        return val

    def set_value(self, obj: Any, path: str, value: Any) -> Any:
        """
        Functional update. Navigates the path and returns a NEW object tree
        with the value applied at the leaf.
        Automatically increments _property_version if the target is a SceneNode.
        """
        parts = path.split(".")
        updated_obj = self._update_recursive(obj, parts, value)

        # Automatic Version Management for SceneNodes
        if isinstance(updated_obj, SceneNode):
            updated_obj.increment_property_version()
        
        return updated_obj

    def _update_recursive(self, obj: Any, parts: list[str], value: Any) -> Any:
        """Helper for immutable recursive replacement."""
        if not parts:
            return value

        part = parts[0]
        remaining = parts[1:]

        # 1. Dictionary Path
        if isinstance(obj, dict):
            new_dict = dict(obj)
            new_dict[part] = self._update_recursive(obj[part], remaining, value)
            return new_dict

        # 2. List Path
        if isinstance(obj, list):
            idx = int(part)
            new_list = list(obj)
            new_list[idx] = self._update_recursive(obj[idx], remaining, value)
            return new_list

        # 2.5 Tuple Path (Immutable)
        if isinstance(obj, tuple):
            try:
                idx = int(part)
                temp_list = list(obj)
                temp_list[idx] = self._update_recursive(obj[idx], remaining, value)
                return tuple(temp_list)
            except (ValueError, IndexError):
                # Fallback: maybe it's an attribute of a namedtuple? 
                # (Though we don't use them currently)
                pass

        # 3. Dataclass Path
        if is_dataclass(obj):
            # Resolve target type for coercion at the leaf
            target_type = None
            if not remaining:
                field_map = {f.name: f.type for f in fields(obj)}
                target_type = field_map.get(part)

            # Recursive step
            current_child = getattr(obj, part)
            new_child = self._update_recursive(current_child, remaining, value)

            # Final leaf coercion
            if not remaining:
                new_child = self._coerce_value(new_child, target_type)

            # Immutable replacement
            try:
                # Try direct mutation first if it's not frozen (for hybrid support during migration)
                setattr(obj, part, new_child)
                return obj
            except Exception:
                # Fallback to immutable replace
                return replace(obj, **{part: new_child})

        # 4. Standard Attribute Path (Fallback)
        if remaining:
            # Recurse into standard object attributes
            current_child = getattr(obj, part)
            new_child = self._update_recursive(current_child, remaining, value)
            setattr(obj, part, new_child)
            return obj

        setattr(obj, part, value)
        return obj

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
        """Helper to convert raw input to the expected Value Object or Primitive."""
        if target_type is None or value is None:
            return value

        # Unwrap Union types
        if get_origin(target_type) is Union:
            args = get_args(target_type)
            # Find the most specific non-None type
            for arg in args:
                if arg is not type(None):
                    target_type = arg
                    break

        # 1. Handle Enums
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            if isinstance(value, str):
                try:
                    return target_type(value)
                except ValueError:
                    return value
            return value

        # 2. Handle Color VO
        if target_type is Color:
            if isinstance(value, Color):
                return value
            return Color.from_mpl(value)

        # 3. Handle Dimension VO
        if target_type is Dimension:
            if isinstance(value, Dimension):
                return value
            # Assume UI spoken units are CM if raw float provided
            return Dimension(float(value), Unit.CM)

        # 4. Handle Refined Primitives
        if target_type is Alpha:
            return Alpha(float(value))
        if target_type is ZOrder:
            return ZOrder(int(value))

        # 5. Handle Tuple coercion
        if get_origin(target_type) is tuple:
            if isinstance(value, (list, tuple)):
                return tuple(value)

        # 6. Standard Numeric Fallback
        if isinstance(value, str):
            try:
                if target_type is float:
                    return float(value)
                if target_type is int:
                    return int(value)
            except ValueError:
                pass

        return value

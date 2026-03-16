# Technical Design Document 5: Transition to DDD Value Objects & Immutable State

## 1. Introduction & Objectives

This document defines the architectural transition from mutable dataclasses and "Primitive Obsession" to a formal **Domain-Driven Design (DDD) Value Object** architecture. The goal is to ensure the integrity of the application's scientific and aesthetic state by enforcing immutability and centralizing domain logic (validation, conversion) within self-contained objects.

### 1.1. Core Objectives:
1.  **Eliminate Side-Effects**: Prevent accidental state changes by making the entire `PlotProperties` tree immutable (`frozen=True`).
2.  **Encapsulate Domain Logic**: Replace raw primitives (strings for colors, floats for dimensions) with objects that "know" their own rules (e.g., a `Color` knows how to validate a Hex string).
3.  **Predictable State Flow**: Transition the `PropertyService` and `StyleService` to a functional, return-based pattern, simplifying the Undo/Redo and Rendering pipelines.
4.  **Unit Safety**: Ensure that physical measurements (cm, inch, pt) are explicitly typed as `Dimension` objects to prevent unit-mismatch bugs.

---

## 2. Architectural Paradigm: The Value Object Pattern

### 2.1. The "Primitive Obsession" Problem
Currently, the codebase represents complex domain concepts using generic types:
*   **Colors**: `Union[str, tuple, list]`. This requires every consumer (Renderer, UI, Service) to implement its own parsing/normalization logic.
*   **Dimensions**: Raw `float`. There is no inherent distinction between a line width of 1.5 *points* and a margin of 1.5 *centimeters*.
*   **Properties**: Mutable dataclasses. Changing `node.properties.visuals.color = "red"` is easy but bypasses the `CommandManager` if done incorrectly, leading to desynchronized Undo history.

### 2.2. The Value Object Solution
We will implement Value Objects adhering to strict DDD principles:
*   **Immutability**: Once created, a value cannot change. Any "update" returns a new instance.
*   **Attribute-based Equality**: Two `Color(1, 0, 0)` objects are identical regardless of memory address.
*   **No Identity**: A `Dimension(1.0, CM)` is just a value; it does not need a `node_id`.

---

## 3. Foundational Data Structures

### 3.1. The `Color` Value Object (`src/shared/color.py`)
A centralized authority for color representation.
*   **Internal State**: `r, g, b, a` (floats 0.0 - 1.0).
*   **Factory Methods**:
    *   `from_hex(hex_str: str)`: Parses CSS-style hex.
    *   `from_mpl(val: Any)`: Handles Matplotlib's varied inputs (named colors, tuples).
*   **Output Methods**:
    *   `to_mpl()`: Returns a `(r, g, b, a)` tuple for Matplotlib.
    *   `to_hex()`: Returns a hex string for UI displays.
*   **Validation**: Raises `ValueError` if components are outside `[0, 1]`.

### 3.2. The `Dimension` & `Unit` Objects (`src/shared/units.py`)
Ensures physical measurements are explicit and convertible.
*   **`Unit` (Enum)**: `CM` (Canonical), `INCH`, `PT`, `PX`.
*   **`Dimension` (Frozen Dataclass)**:
    *   **Attributes**: `value: float`, `unit: Unit`.
    *   **Logic**: `to_cm()`, `to_pt()`, `to_inch()` using standard conversion factors.
    *   **Arithmetic**: Supports `dimension * scalar` for scaling operations.

### 3.3. Refined Primitives (Subclassed Primitives)
For single-value concepts requiring direct math support:
*   **`Alpha(float)`**: Enforces `0.0 <= x <= 1.0`.
*   **`ZOrder(int)`**: Enforces `x >= 0`.

---

## 4. Service & Infrastructure Refactoring

### 4.1. Functional `PropertyService` (`src/services/property_service.py`)
The service must move from **In-place Mutation** to **Recursive Replacement**.
*   **Return-based API**: `set_value(root, path, value) -> NewRoot`.
*   **Logic (Recursive Replacement)**: 
    1.  Navigate to the leaf.
    2.  Coerce the `value` into a `Color` or `Dimension` if needed.
    3.  Use `dataclasses.replace()` on the parent.
    4.  Recursively bubble the new parent up to the root.
*   **Primitive Projection (UI Integration)**: To prevent "UI Boilerplate," the service will implement a `get_projected_value(root, path)` method. This method acts as a **Read Model / Projection** layer that automatically "unwraps" Value Objects into the primitives required by UI widgets (e.g., `Dimension -> float`, `Color -> hex string`). This keeps the View "dumb" and the Domain "rich."
*   **Example**: Changing a color at `coords.xaxis.label.color` results in a new `LabelProperties`, which triggers a new `AxisProperties`, and finally a new `PlotProperties` root.

### 4.2. Pure `StyleService` (`src/services/style_service.py`)
The `hydrate()` method will be refactored to be a pure function.
*   **Logic**: Instead of `setattr(obj, key, val)`, it will calculate a dictionary of changes and return `replace(obj, **changes)`.
*   **Factory Integrity**: All `_create_...` methods (e.g., `_create_line`) will now return hierarchies of frozen VOs and properly initialized `Color`/`Dimension` objects.

---

## 5. Model Integrity: The Frozen Hierarchy

### 5.1. Freezing `PlotProperties` (`src/models/plots/plot_properties.py`)
Every dataclass in this file (Line, Font, Axis, etc.) will be marked `frozen=True`.
*   **Impact**: Any accidental attempt to mutate a property in a Controller or Renderer will trigger a `FrozenInstanceError` during development, forcing adherence to the Command Pattern.
*   **Type Update**:
    ```python
    @dataclass(frozen=True)
    class LineProperties:
        color: Color  # Was Union[str, tuple, list]
        linewidth: Dimension  # Was float
        # ...
    ```

### 5.2. Freezing `GridPosition` (`src/models/nodes/grid_position.py`)
Ensures that a node's location in a grid is a fixed "fact" that can only be changed by a formal layout command.

---

## 6. Implementation Sequence

### Phase 1: Foundations (The VOs)
1.  Implement `Color`, `Unit`, and `Dimension` in `src/shared/`.
2.  Write exhaustive unit tests for conversions and validations.

### Phase 2: Infrastructure (The Services)
1.  Refactor `PropertyService.set_value` to the return-based recursive pattern.
2.  Update `PropertyService._coerce_value` to handle automatic VO instantiation.
3.  Refactor `StyleService.hydrate` to be functional.

### Phase 3: The Big Freeze (The Models)
1.  Apply `frozen=True` to `GridPosition`.
2.  Apply `frozen=True` to the entire `PlotProperties` hierarchy.
3.  Update all property type hints to use the new VOs.

### Phase 4: Integration (The Consumers)
1.  Update `ChangePlotPropertyCommand` to handle the new return values.
2.  Update `FigureRenderer` to call `color.to_mpl()`.
3.  Update `CoordinateService` to leverage the `Dimension` conversion logic.

---

## 7. Risks & Mitigations

*   **Risk: Memory Pressure**: Creating many small immutable objects during high-frequency updates (e.g., dragging a slider).
    *   **Mitigation**: Python's garbage collection is highly optimized for short-lived objects. Use `__slots__` where performance is critical.
*   **Risk: Boilerplate in UI**: Extracting raw values for UI widgets (e.g., getting `float` from `Dimension` for a spinbox).
    *   **Mitigation**: Implement a `PropertyService.get_raw_value()` that automatically unwraps VOs for the UI layer.
*   **Risk: Breaking Deserialization**: `PlotProperties.from_dict` failing due to frozen constructors.
    *   **Mitigation**: The existing `_from_dict_recursive` helper already uses constructor-based instantiation, which is compatible with frozen dataclasses.

---

**Approved by:** Gemini CLI / Lead Architect  
**Status:** Approved  
**Target Version:** 2.0.0 (DDD-Alignment)

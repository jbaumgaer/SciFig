from __future__ import annotations

class Alpha(float):
    """
    A refined primitive representing transparency.
    Enforces a domain constraint of [0.0, 1.0].
    """
    def __new__(cls, value: float):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Alpha must be between 0.0 and 1.0, got {value}")
        return super().__new__(cls, value)

class ZOrder(int):
    """
    A refined primitive representing rendering depth.
    Enforces a domain constraint of [0, inf).
    """
    def __new__(cls, value: int):
        if value < 0:
            raise ValueError(f"ZOrder must be non-negative, got {value}")
        return super().__new__(cls, value)

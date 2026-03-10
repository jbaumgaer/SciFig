from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Rect:
    """
    A robust geometric primitive representing a rectangle in physical 
    centimeters (cm).
    
    This class is immutable (frozen) to ensure coordinate integrity during 
    complex layout calculations.
    """
    x: float
    y: float
    width: float
    height: float

    def moved_by(self, dx: float, dy: float) -> "Rect":
        """Returns a new Rect moved by the specified offsets."""
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def scaled_by(self, anchor: str, dx: float, dy: float) -> "Rect":
        """
        Returns a new Rect scaled based on a specific anchor point.
        
        Args:
            anchor: One of 'top-left', 'top-right', 'bottom-left', 'bottom-right',
                    'top', 'bottom', 'left', 'right'.
            dx: Change in x direction.
            dy: Change in y direction.
        """
        new_x, new_y, new_w, new_h = self.x, self.y, self.width, self.height

        if "left" in anchor:
            new_x += dx
            new_w -= dx
        elif "right" in anchor:
            new_w += dx

        if "bottom" in anchor:
            new_y += dy
            new_h -= dy
        elif "top" in anchor:
            new_h += dy

        # Ensure we don't flip the rectangle inside out
        # (Min size threshold of 0.1 cm as per TDD-5)
        new_w = max(0.1, new_w)
        new_h = max(0.1, new_h)

        return Rect(new_x, new_y, new_w, new_h)

    def contains(self, x: float, y: float) -> bool:
        """Returns True if the point (x, y) is within the rectangle."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)

    def intersects(self, other: "Rect") -> bool:
        """Returns True if this rectangle overlaps with another."""
        return not (self.x + self.width < other.x or
                    other.x + other.width < self.x or
                    self.y + self.height < other.y or
                    other.y + other.height < self.y)

    def clamp_to_bounds(self, xmin: float, ymin: float, xmax: float, ymax: float) -> "Rect":
        """Returns a new Rect constrained within the specified bounds."""
        new_x = max(xmin, min(self.x, xmax - self.width))
        new_y = max(ymin, min(self.y, ymax - self.height))
        return Rect(new_x, new_y, self.width, self.height)

    def get_center(self) -> tuple[float, float]:
        """Returns the (x, y) coordinates of the rectangle's center."""
        return self.x + self.width / 2, self.y + self.height / 2

    @classmethod
    def from_center(cls, cx: float, cy: float, w: float, h: float) -> "Rect":
        """Creates a Rect centered at (cx, cy) with the given dimensions."""
        return cls(cx - w / 2, cy - h / 2, w, h)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Returns the geometry as a (left, bottom, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)

    @classmethod
    def from_tuple(cls, t: tuple[float, float, float, float]) -> "Rect":
        """Creates a Rect from a (left, bottom, width, height) tuple."""
        return cls(t[0], t[1], t[2], t[3])

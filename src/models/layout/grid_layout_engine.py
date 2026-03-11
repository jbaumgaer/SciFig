import logging
from typing import Dict, Optional, Tuple

from src.models.nodes.grid_node import GridNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.shared.geometry import Rect


class GridLayoutEngine:
    """
    A recursive mathematical layout engine for GridNodes.
    Calculates absolute physical geometries (CM) for all children 
    without relying on Matplotlib's GridSpec.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("GridLayoutEngine initialized.")

    def calculate_geometries(
        self, 
        root_grid: GridNode, 
        figure_size_cm: Tuple[float, float]
    ) -> None:
        """
        Calculates and updates the geometry properties of all descendants 
        of the root_grid.
        """
        fig_w, fig_h = figure_size_cm
        initial_rect = Rect(0.0, 0.0, fig_w, fig_h)
        
        # Ensure the root grid itself knows its bounds
        root_grid.geometry = initial_rect
        root_grid._geometry_version += 1
        
        self._calculate_recursive(root_grid, initial_rect)

    def get_cell_geometries(self, grid_node: GridNode, available_rect: Rect) -> list[list[Rect]]:
        """
        Returns a 2D list [row][col] of Rects representing the individual 
        cell boundaries (spines) for the given grid_node using Matplotlib (Bottom-Up) Y.
        """
        # 1. Deduct Margins (Using Matplotlib Space: Bottom is net_rect.y)
        m = grid_node.margins
        net_rect = Rect(
            x=available_rect.x + m.left,
            y=available_rect.y + m.bottom, # Start from bottom
            width=available_rect.width - (m.left + m.right),
            height=available_rect.height - (m.top + m.bottom)
        )

        # 2. Calculate Cell Dimensions
        total_w_space = sum(grid_node.gutters.wspace)
        total_h_space = sum(grid_node.gutters.hspace)
        pure_w = net_rect.width - total_w_space
        pure_h = net_rect.height - total_h_space

        col_widths = [(r / sum(grid_node.col_ratios)) * pure_w for r in grid_node.col_ratios]
        row_heights = [(r / sum(grid_node.row_ratios)) * pure_h for r in grid_node.row_ratios]

        # 3. Build the Grid
        # X: Left to Right
        col_xs = [net_rect.x]
        current_x = net_rect.x
        for i in range(len(col_widths) - 1):
            current_x += col_widths[i] + grid_node.gutters.wspace[i]
            col_xs.append(current_x)

        # Y: Bottom to Top (Reverse indices so Row 0 is at top)
        # We calculate row start positions starting from the bottom of net_rect
        row_ys_bottom_up = [net_rect.y]
        current_y = net_rect.y
        for i in range(len(row_heights) - 1, 0, -1):
            current_y += row_heights[i] + grid_node.gutters.hspace[i-1]
            row_ys_bottom_up.insert(0, current_y) 
        
        # At this point row_ys_bottom_up[0] is the Y of Row 0 (the top row)
        row_ys = row_ys_bottom_up

        # 4. Generate the 2D Rect Array
        cells = []
        num_rows = len(row_heights)
        num_cols = len(col_widths)
        for r in range(num_rows):
            row_cells = []
            for c in range(num_cols):
                row_cells.append(Rect(col_xs[c], row_ys[r], col_widths[c], row_heights[r]))
            cells.append(row_cells)
        
        return cells

    def _calculate_recursive(self, grid_node: GridNode, available_rect: Rect) -> None:
        """
        Recursively calculates geometries for a single GridNode's children.
        Uses Bottom-Up (Matplotlib) coordinates.
        """
        cells = self.get_cell_geometries(grid_node, available_rect)
        grid_node.cell_geometries = cells # Cache the atomic lattice for UI/Interaction
        
        # Assign Geometries to Children
        for child in grid_node.children:
            if not child.grid_position:
                self.logger.warning(f"Child {child.name} in GridNode has no grid_position. Skipping.")
                continue

            pos = child.grid_position
            
            # Boundary checks
            if pos.row >= grid_node.rows or pos.col >= grid_node.cols:
                self.logger.error(f"Child {child.name} position {pos} out of bounds for {grid_node.rows}x{grid_node.cols}")
                continue

            # Calculate child span based on the pre-calculated cell grid
            top_left_cell = cells[pos.row][pos.col]
            
            # Find bottom-right cell of the span
            last_row = pos.row + pos.rowspan - 1
            last_col = pos.col + pos.colspan - 1
            
            # Clamp span to grid boundaries
            last_row = min(last_row, len(cells) - 1)
            last_col = min(last_col, len(cells[0]) - 1)
            
            bottom_right_cell = cells[last_row][last_col]

            child_x = top_left_cell.x
            # In Bottom-Up, the 'y' of the spanned rect is the 'y' of the BOTTOM-most cell
            child_y = bottom_right_cell.y
            
            child_w = (bottom_right_cell.x + bottom_right_cell.width) - top_left_cell.x
            child_h = (top_left_cell.y + top_left_cell.height) - bottom_right_cell.y

            new_geom = Rect(child_x, child_y, child_w, child_h)

            # 7. Update Geometry and Version if changed
            if child.geometry != new_geom:
                child.geometry = new_geom
                child._geometry_version += 1
                self.logger.debug(f"Updated geometry for {child.name} to {new_geom} (v{child._geometry_version})")

            # 8. Recursion / Specialized Handling
            if isinstance(child, GridNode):
                self._calculate_recursive(child, new_geom)
            elif not isinstance(child, PlotNode):
                # TDD 4.1: If a ShapeNode or TextNode is assigned to a cell, 
                # center it horizontally and vertically.
                # (Placeholder for future implementation)
                pass

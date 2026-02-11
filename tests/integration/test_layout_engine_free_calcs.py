"""
Integration tests for FreeLayoutEngine's alignment and distribution calculations.
"""

import pytest

from src.models.nodes.plot_node import PlotNode


def test_free_layout_engine_aligns_geometries(real_free_layout_engine):
    """
    Integration Test: FreeLayoutEngine aligns geometries.
    This test should:
    - Initialize a real FreeLayoutEngine.
    - Create several mock PlotNodes with varied initial geometries.
    - Call FreeLayoutEngine.perform_align('left') for these plots.
    - Assert that the returned geometries have the same minimum X coordinate.
    - Repeat for other alignment edges (right, top, bottom, center, middle).
    """
    engine = real_free_layout_engine

    plot1 = PlotNode()
    plot1.geometry = (0.1, 0.4, 0.2, 0.2)
    plot2 = PlotNode()
    plot2.geometry = (0.5, 0.1, 0.2, 0.2)
    plot3 = PlotNode()
    plot3.geometry = (0.3, 0.7, 0.2, 0.2)
    plots = [plot1, plot2, plot3]

    # Align Left
    geometries_left = engine.perform_align(plots, "left")
    min_x = min([p.geometry[0] for p in plots])
    for geom in geometries_left.values():
        assert geom[0] == min_x

    # Align Right
    geometries_right = engine.perform_align(plots, "right")
    max_right = max([p.geometry[0] + p.geometry[2] for p in plots])
    for plot_id, geom in geometries_right.items():
        plot = next(p for p in plots if p.id == plot_id)
        assert geom[0] + geom[2] == max_right

    # Align Top
    geometries_top = engine.perform_align(plots, "top")
    min_y = min([p.geometry[1] for p in plots])
    for geom in geometries_top.values():
        assert geom[1] == min_y

    # Align Bottom
    geometries_bottom = engine.perform_align(plots, "bottom")
    max_bottom = max([p.geometry[1] + p.geometry[3] for p in plots])
    for plot_id, geom in geometries_bottom.items():
        plot = next(p for p in plots if p.id == plot_id)
        assert geom[1] + geom[3] == max_bottom

    # Align Horizontal Center
    geometries_hcenter = engine.perform_align(plots, "h_center")
    # Calculate the center of the bounding box of all plots
    min_x = min(p.geometry[0] for p in plots)
    max_x_plus_width = max(p.geometry[0] + p.geometry[2] for p in plots)
    center_x = (min_x + max_x_plus_width) / 2
    for plot_id, geom in geometries_hcenter.items():
        plot = next(p for p in plots if p.id == plot_id)
        assert (geom[0] + geom[2] / 2) == pytest.approx(center_x, abs=1e-9)

    # Align Vertical Center
    geometries_vcenter = engine.perform_align(plots, "v_center")
    min_y = min(p.geometry[1] for p in plots)
    max_y_plus_height = max(p.geometry[1] + p.geometry[3] for p in plots)
    center_y = (min_y + max_y_plus_height) / 2
    for plot_id, geom in geometries_vcenter.items():
        plot = next(p for p in plots if p.id == plot_id)
        assert (geom[1] + geom[3] / 2) == pytest.approx(center_y, abs=1e-9)


def test_free_layout_engine_distributes_geometries(real_free_layout_engine):
    """
    Integration Test: FreeLayoutEngine distributes geometries.
    This test should:
    - Initialize a real FreeLayoutEngine.
    - Create at least three mock PlotNodes with varied initial geometries.
    - Call FreeLayoutEngine.perform_distribute('horizontal') for these plots.
    - Assert that the returned geometries have evenly distributed horizontal spacing.
    - Repeat for vertical distribution.
    """
    engine = real_free_layout_engine

    plot1 = PlotNode()
    plot1.geometry = (0.1, 0.1, 0.1, 0.1)  # x=0.1, width=0.1 -> right=0.2
    plot2 = PlotNode()
    plot2.geometry = (0.5, 0.2, 0.2, 0.2)  # x=0.5, width=0.2 -> right=0.7
    plot3 = PlotNode()
    plot3.geometry = (0.8, 0.3, 0.1, 0.1)  # x=0.8, width=0.1 -> right=0.9
    plots = [plot1, plot2, plot3]

    # Distribute Horizontally
    geometries_h = engine.perform_distribute(plots, "horizontal")

    # Re-sort plots by their new x-coordinates to correctly calculate gaps
    sorted_plots_h = sorted(plots, key=lambda p: geometries_h[p.id][0])

    gaps_h = []
    for i in range(len(sorted_plots_h) - 1):
        p1_id = sorted_plots_h[i].id
        p2_id = sorted_plots_h[i + 1].id
        gap = geometries_h[p2_id][0] - (geometries_h[p1_id][0] + geometries_h[p1_id][2])
        gaps_h.append(gap)

    # Assert that gaps are approximately equal
    for i in range(len(gaps_h) - 1):
        assert abs(gaps_h[i] - gaps_h[i + 1]) < 1e-9

    # Distribute Vertically
    plot1.geometry = (0.1, 0.1, 0.1, 0.1)  # y=0.1, height=0.1 -> bottom=0.2
    plot2.geometry = (0.2, 0.5, 0.2, 0.2)  # y=0.5, height=0.2 -> bottom=0.7
    plot3 = PlotNode()
    plot3.geometry = (0.3, 0.8, 0.1, 0.1)  # y=0.8, height=0.1 -> bottom=0.9

    geometries_v = engine.perform_distribute(plots, "vertical")

    # Extract top-most (y) and bottom-most (y + height) coordinates
    plot_tops = sorted([geometries_v[p.id][1] for p in plots])

    # Calculate spacing between top edges
    spacing1_v = plot_tops[1] - plot_tops[0]
    spacing2_v = plot_tops[2] - plot_tops[1]

    # Expect approximately equal spacing (allow for float precision)
    assert abs(spacing1_v - spacing2_v) < 1e-9

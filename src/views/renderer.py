import matplotlib.figure
import matplotlib.patches as patches
import pandas as pd

from src.models.nodes import PlotNode, SceneNode
from src.models.nodes.plot_types import PlotType
from .plotting_strategies import LinePlotStrategy, ScatterPlotStrategy


class Renderer:
    """
    A class responsible for rendering the scene graph onto a Matplotlib figure.
    """

    def __init__(self):
        self.plotting_strategies = {
            PlotType.LINE: LinePlotStrategy(),
            PlotType.SCATTER: ScatterPlotStrategy(),
        }

    def render(
        self,
        figure: matplotlib.figure.Figure,
        root_node: SceneNode,
        selection: list[SceneNode],
    ):
        """
        Renders the entire scene graph, starting from the root node.
        Also draws highlights for the currently selected nodes.
        """
        figure.clear()
        self._render_node(figure, root_node)
        self._render_highlights(figure, selection)

    def _render_node(self, figure: matplotlib.figure.Figure, node: SceneNode):
        """
        Recursively renders a node and its children.
        """
        if not node.visible:
            return

        # --- Render the node itself based on its type ---
        if isinstance(node, PlotNode):
            ax = figure.add_axes(node.geometry)

            if node.plot_properties:
                props = node.plot_properties
                # 1. Plot data based on configuration
                if isinstance(node.data, pd.DataFrame):
                    strategy = self.plotting_strategies.get(props.plot_type)
                    mapping = props.plot_mapping
                    if strategy and mapping and mapping.x and mapping.y:
                        strategy.plot(ax, node.data, mapping.x, mapping.y)
                    # Optional: Could add a default plotting call here if strategy is not found
                    elif node.data.shape[1] >= 2:
                        # Default plot if no mapping or strategy
                        col1, col2 = node.data.columns[0], node.data.columns[1]
                        ax.plot(node.data[col1], node.data[col2])

                # 2. Apply labels and title
                ax.set_title(props.title)
                ax.set_xlabel(props.xlabel)
                ax.set_ylabel(props.ylabel)

                # 3. Apply axes limits
                limits = props.axes_limits
                if limits.xlim[0] is not None or limits.xlim[1] is not None:
                    ax.set_xlim(limits.xlim)
                if limits.ylim[0] is not None or limits.ylim[1] is not None:
                    ax.set_ylim(limits.ylim)
            else:
                # Draw an empty axes if no data or properties
                ax.tick_params(
                    axis="both",
                    which="both",
                    bottom=False,
                    top=False,
                    left=False,
                    right=False,
                    labelbottom=False,
                    labelleft=False,
                )

        # --- Recursively render children ---
        for child in node.children:
            self._render_node(figure, child)

    def _render_highlights(
        self, figure: matplotlib.figure.Figure, selection: list[SceneNode]
    ):
        """
        Draws highlight rectangles for all selected nodes.
        """
        for node in selection:
            if isinstance(node, PlotNode):  # For now, we only highlight plots
                left, b, w, h = node.geometry
                highlight = patches.Rectangle(
                    (left, b),
                    w,
                    h,
                    facecolor="none",
                    edgecolor="cornflowerblue",
                    linewidth=2,
                    transform=figure.transFigure,
                    clip_on=False,
                    # High zorder to appear on top
                    zorder=1000,
                )
                figure.add_artist(highlight)

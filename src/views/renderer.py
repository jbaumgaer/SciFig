import matplotlib.figure
import matplotlib.patches as patches
import pandas as pd

from src.models.nodes import PlotNode, SceneNode


class Renderer:
    """
    A class responsible for rendering the scene graph onto a Matplotlib figure.
    """

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
                    df = node.data
                    mapping = props.plot_mapping

                    if mapping and mapping.x and mapping.y:
                        x_col, y_cols = mapping.x, mapping.y
                        for y_col in y_cols:
                            if x_col in df.columns and y_col in df.columns:
                                ax.plot(df[x_col], df[y_col], label=y_col)
                        if len(y_cols) > 1:
                            ax.legend()
                    elif df.shape[1] >= 2:
                        # Default plot if no mapping
                        col1, col2 = df.columns[0], df.columns[1]
                        ax.plot(df[col1], df[col2])

                # 2. Apply labels and title
                ax.set_title(props.title)
                ax.set_xlabel(props.xlabel)
                ax.set_ylabel(props.ylabel)

                # 3. Apply axes limits
                limits = props.axes_limits
                if limits.xlim:
                    ax.set_xlim(limits.xlim)
                if limits.ylim:
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

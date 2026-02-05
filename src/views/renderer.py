import logging 
import matplotlib.figure
import matplotlib.patches as patches
import pandas as pd
import matplotlib.axes # Import matplotlib.axes

from src.models.nodes import PlotNode, RectangleNode, SceneNode, TextNode, GroupNode
from src.models.nodes.plot_types import PlotType
from src.config_service import ConfigService 
from src.models.application_model import ApplicationModel 

from .plotting_strategies import LinePlotStrategy, ScatterPlotStrategy


class Renderer:
    """
    A class responsible for rendering the scene graph onto a Matplotlib figure.
    """

    def __init__(self, config_service: ConfigService, application_model: ApplicationModel): 
        self._config_service = config_service 
        self._application_model = application_model 
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Renderer initialized.")

        self.plotting_strategies = {
            PlotType.LINE: LinePlotStrategy(),
            PlotType.SCATTER: ScatterPlotStrategy(),
        }
        self.logger.debug(f"Plotting strategies: {list(self.plotting_strategies.keys())}")

        self._render_strategies = {
            GroupNode: self._render_group_node,
            PlotNode: self._render_plot_node,
            # RectangleNode: self._render_rectangle_node, # To be added later
        }
        self.logger.debug(f"Render strategies: {list(self._render_strategies.keys())}")


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
        self.logger.info("Rendering scene graph.")
        figure.clear()

        if self._application_model.auto_layout_enabled:
            self.logger.debug("Auto-layout is enabled. Applying constrained_layout.")
            figure.set_constrained_layout(True)
        elif self._application_model.figure_subplot_params:
            self.logger.debug(f"Auto-layout is disabled. Applying captured subplot parameters: {self._application_model.figure_subplot_params}")
            figure.subplots_adjust(**self._application_model.figure_subplot_params)
        else:
            self.logger.debug("Auto-layout is disabled and no subplot parameters captured. Skipping layout adjustment.")


        self._render_node(figure, root_node)
        self._render_highlights(figure, selection)
        self.logger.info("Scene graph rendering complete.")


    def _render_node(self, figure: matplotlib.figure.Figure, node: SceneNode):
        """
        Dispatches rendering of a node based on its type.
        The specific render function is responsible for rendering the node
        and recursively calling _render_node for its children if it's a composite node.
        """
        if not node.visible:
            self.logger.debug(f"Node {node.name} (ID: {node.id}) is not visible. Skipping rendering.")
            return

        render_func = self._render_strategies.get(type(node))
        if render_func:
            render_func(figure, node)
        else:
            self.logger.warning(f"No renderer found for node type {type(node).__name__}. Node ID: {node.id}, Name: {node.name}")

    def _render_group_node(self, figure: matplotlib.figure.Figure, node: GroupNode):
        """
        Renders a GroupNode by recursively rendering its children.
        A GroupNode itself has no direct visual representation.
        """
        self.logger.debug(f"Rendering GroupNode: {node.name} (ID: {node.id}), Children: {len(node.children)}")
        for child in node.children:
            self._render_node(figure, child)

    def _render_plot_node(self, figure: matplotlib.figure.Figure, node: PlotNode):
        """
        Renders a single PlotNode.
        """
        self.logger.debug(f"Rendering PlotNode: {node.name} (ID: {node.id}), Geometry: {node.geometry}")
        ax = figure.add_axes(node.geometry)
        node.axes = ax # Assign the created Axes object to the node

        if node.plot_properties:
            props = node.plot_properties
            self.logger.debug(f"  PlotType: {props.plot_type}, Title: {props.title}")
            # 1. Plot data based on configuration
            if isinstance(node.data, pd.DataFrame):
                strategy = self.plotting_strategies.get(props.plot_type)
                mapping = props.plot_mapping
                if strategy and mapping and mapping.x and mapping.y:
                    strategy.plot(ax, node.data, mapping.x, mapping.y)
                    self.logger.debug(f"  Plotted data using {props.plot_type} strategy for {node.name}.") # Added log
                elif node.data.shape[1] >= 2:
                    col1, col2 = node.data.columns[0], node.data.columns[1]
                    ax.plot(node.data[col1], node.data[col2])
                    self.logger.debug(f"  Plotted default data for {node.name} (cols {col1}, {col2}).") # Added log
                else:
                    self.logger.warning(f"  PlotNode '{node.name}' has data but no suitable strategy or mapping found.") # Added log

            # 2. Apply labels and title
            ax.set_title(props.title)
            ax.set_xlabel(props.xlabel)
            ax.set_ylabel(props.ylabel)
            self.logger.debug(f"  Applied title '{props.title}', xlabel '{props.xlabel}', ylabel '{props.ylabel}' to {node.name}.") # Added log


            # 3. Apply axes limits
            limits = props.axes_limits
            if limits.xlim[0] is not None or limits.xlim[1] is not None:
                ax.set_xlim(limits.xlim)
                self.logger.debug(f"  Applied x-limits {limits.xlim} to {node.name}.") # Added log
            if limits.ylim[0] is not None or limits.ylim[1] is not None:
                ax.set_ylim(limits.ylim)
                self.logger.debug(f"  Applied y-limits {limits.ylim} to {node.name}.") # Added log
        else:
            self.logger.debug(f"  PlotNode {node.name} has no plot_properties. Drawing empty axes.") # Added log
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

    def _render_rectangle_node(
        self, figure: matplotlib.figure.Figure, node: "RectangleNode"
    ):
        """
        Renders a single RectangleNode.
        """
        self.logger.debug(f"Rendering RectangleNode: {node.name} (ID: {node.id}). (Placeholder)") # Added log
        # Placeholder for rendering a rectangle
        pass

    def _render_text_node(self, figure: matplotlib.figure.Figure, node: "TextNode"):
        """
        Renders a single TextNode.
        """
        self.logger.debug(f"Rendering TextNode: {node.name} (ID: {node.id}). (Placeholder)") # Added log
        # Placeholder for rendering text
        pass

    def _render_highlights(
        self, figure: matplotlib.figure.Figure, selection: list[SceneNode]
    ):
        """
        Draws highlight rectangles for all selected nodes.
        """
        if selection:
            self.logger.debug(f"Rendering highlights for {len(selection)} selected nodes.") # Added log
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
                self.logger.debug(f"  Highlight rendered for PlotNode: {node.name} (ID: {node.id}).") # Added log

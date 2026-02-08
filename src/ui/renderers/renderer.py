import logging

import matplotlib.figure
import matplotlib.patches as patches
import pandas as pd

from src.shared.constants import LayoutMode
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.nodes.scene_node import SceneNode
from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.rectangle_node import RectangleNode
from src.models.nodes.text_node import TextNode
from src.models.plots.plot_types import PlotType

from src.ui.renderers.plotting_strategies import LinePlotStrategy, ScatterPlotStrategy


class Renderer:
    """
    A class responsible for rendering the scene graph onto a Matplotlib figure.
    """

    def __init__(self, layout_manager: LayoutManager, application_model: ApplicationModel): # Modified signature
        self._layout_manager = layout_manager
        self._application_model = application_model
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Renderer initialized.")

        self.plotting_strategies = {
            PlotType.LINE: LinePlotStrategy(),
            PlotType.SCATTER: ScatterPlotStrategy(),
        }
        self.logger.debug(f"Plotting strategies: {list(self.plotting_strategies.keys())}")

        self._render_strategies = {
            # GroupNode rendering will now be handled directly in _render_node or render()
            # PlotNode rendering (axis creation and data plotting) is handled in render()
            # This dictionary might be used for other SceneNode types in the future
            # e.g., TextNode: self._render_text_node
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

        self._render_plots(figure)  # New helper for plot nodes

        # Render other node types (TextNode, RectangleNode, GroupNode)
        self._render_other_nodes(figure, root_node)  # Modified _render_node

        self._render_highlights(figure, selection)
        self.logger.info("Scene graph rendering complete.")

    def _render_plots(self, figure: matplotlib.figure.Figure):
        """
        Renders all PlotNodes on the figure based on calculated geometries.
        """
        plot_nodes = [
            node
            for node in self._application_model.scene_root.all_descendants()
            if isinstance(node, PlotNode)
        ]

        calculated_geometries = self._layout_manager.get_current_layout_geometries(
            plot_nodes
        )

        for plot_node in plot_nodes:
            if plot_node.id in calculated_geometries:
                geometry = calculated_geometries[plot_node.id]
                self.logger.debug(
                    f"Rendering PlotNode: {plot_node.name} (ID: {plot_node.id}), Geometry: {geometry}"
                )
                ax = figure.add_axes(geometry)
                plot_node.axes = ax  # Assign the created Axes object to the node

                if plot_node.plot_properties:
                    props = plot_node.plot_properties
                    self.logger.debug(f"  PlotType: {props.plot_type}, Title: {props.title}")
                    if isinstance(plot_node.data, pd.DataFrame):
                        strategy = self.plotting_strategies.get(props.plot_type)
                        mapping = props.plot_mapping
                        if strategy and mapping and mapping.x and mapping.y:
                            strategy.plot(ax, plot_node.data, mapping.x, mapping.y)
                            self.logger.debug(
                                f"  Plotted data using {props.plot_type} strategy for {plot_node.name}."
                            )
                        elif plot_node.data.shape[1] >= 2:
                            col1, col2 = plot_node.data.columns[0], plot_node.data.columns[1]
                            ax.plot(plot_node.data[col1], plot_node.data[col2])
                            self.logger.debug(
                                f"  Plotted default data for {plot_node.name} (cols {col1}, {col2})."
                            )
                        else:
                            self.logger.warning(
                                f"  PlotNode '{plot_node.name}' has data but no suitable strategy or mapping found."
                            )

                    ax.set_title(props.title)
                    ax.set_xlabel(props.xlabel)
                    ax.set_ylabel(props.ylabel)
                    self.logger.debug(
                        f"  Applied title '{props.title}', xlabel '{props.xlabel}', ylabel '{props.ylabel}' to {plot_node.name}."
                    )

                    limits = props.axes_limits
                    if limits.xlim[0] is not None or limits.xlim[1] is not None:
                        ax.set_xlim(limits.xlim)
                        self.logger.debug(
                            f"  Applied x-limits {limits.xlim} to {plot_node.name}."
                        )
                    if limits.ylim[0] is not None or limits.ylim[1] is not None:
                        ax.set_ylim(limits.ylim)
                        self.logger.debug(
                            f"  Applied y-limits {limits.ylim} to {plot_node.name}."
                        )
                else:
                    self.logger.debug(
                        f"  PlotNode {plot_node.name} has no plot_properties. Drawing empty axes."
                    )
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
            else:
                self.logger.warning(
                    f"No calculated geometry found for PlotNode {plot_node.name} (ID: {plot_node.id}). Skipping rendering of this plot."
                )

        if self._application_model.current_layout_config.mode == LayoutMode.GRID:
            self.logger.debug("Applying constrained_layout for GRID mode.")
            figure.set_constrained_layout(True)

    def _render_other_nodes(self, figure: matplotlib.figure.Figure, node: SceneNode):
        """
        Dispatches rendering of a node based on its type, excluding PlotNodes.
        The specific render function is responsible for rendering the node
        and recursively calling _render_other_nodes for its children if it's a composite node.
        """
        if not node.visible or isinstance(node, PlotNode):  # Skip PlotNodes here
            self.logger.debug(f"Node {node.name} (ID: {node.id}) is not visible or is a PlotNode. Skipping rendering.")
            return

        render_func = self._render_strategies.get(type(node))
        if render_func:
            render_func(figure, node)
        else:
            # For GroupNodes, we need to recursively render children
            if isinstance(node, GroupNode):
                self.logger.debug(f"Rendering GroupNode: {node.name} (ID: {node.id}), Children: {len(node.children)}")
                for child in node.children:
                    self._render_other_nodes(figure, child)  # Recursive call
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



    def _render_rectangle_node(
        self, figure: matplotlib.figure.Figure, node: "RectangleNode"
    ):
        """
        Renders a single RectangleNode.
        """
        self.logger.debug(f"Rendering RectangleNode: {node.name} (ID: {node.id}). (Placeholder)")
        # Placeholder for rendering a rectangle
        pass

    def _render_text_node(self, figure: matplotlib.figure.Figure, node: "TextNode"):
        """
        Renders a single TextNode.
        """
        self.logger.debug(f"Rendering TextNode: {node.name} (ID: {node.id}). (Placeholder)")
        # Placeholder for rendering text
        pass

    def _render_highlights(
        self, figure: matplotlib.figure.Figure, selection: list[SceneNode]
    ):
        """
        Draws highlight rectangles for all selected nodes.
        "TODO: These default values should be moved to the config
        """
        if selection:
            self.logger.debug(f"Rendering highlights for {len(selection)} selected nodes.")
        for node in selection:
            if isinstance(node, PlotNode):  # For now, we only highlight plots
                left, bottom, width, height = node.geometry
                highlight = patches.Rectangle(
                    (left, bottom),
                    width,
                    height,
                    facecolor="none",
                    edgecolor="cornflowerblue",
                    linewidth=2,
                    transform=figure.transFigure,
                    clip_on=False,
                    # High zorder to appear on top
                    zorder=1000,
                )
                figure.add_artist(highlight)
                self.logger.debug(f"  Highlight rendered for PlotNode: {node.name} (ID: {node.id}).")

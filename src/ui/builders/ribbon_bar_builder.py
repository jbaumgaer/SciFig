from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QHBoxLayout

from src.services.event_aggregator import EventAggregator
from src.shared.constants import IconPath
from src.ui.widgets.ribbon_bar import RibbonBar, RibbonGroup


@dataclass
class RibbonActions:
    """
    Container for all actions created in the Ribbon Bar.
    """
    # Insert Tab
    insert_line_action: QAction
    insert_scatter_action: QAction
    insert_bar_action: QAction
    insert_area_action: QAction
    insert_pie_action: QAction
    insert_histogram_action: QAction
    insert_candlestick_action: QAction
    insert_contour_action: QAction
    insert_waterfall_action: QAction
    insert_stairs_action: QAction
    
    insert_arrow_right_action: QAction
    insert_arrow_bottom_right_action: QAction
    
    insert_square_action: QAction
    insert_rectangle_action: QAction
    insert_circle_action: QAction
    insert_pentagon_action: QAction
    insert_hexagon_action: QAction
    
    insert_text_field_action: QAction
    insert_text_action: QAction
    insert_bullet_list_action: QAction
    insert_numbered_list_action: QAction
    insert_check_list_action: QAction
    
    insert_symbol_action: QAction
    insert_formula_action: QAction
    
    # Design Tab
    design_nature_action: QAction
    design_science_action: QAction
    design_cell_action: QAction
    design_colors_action: QAction
    design_fonts_action: QAction
    
    # Layout Tab
    layout_margins_action: QAction
    layout_format_action: QAction
    layout_grid_toggle_action: QAction
    layout_align_left_action: QAction
    layout_align_right_action: QAction
    layout_align_top_action: QAction
    layout_align_bottom_action: QAction
    layout_distribute_h_action: QAction
    layout_distribute_v_action: QAction


class RibbonBarBuilder:
    """
    Builder class to construct the Ribbon Bar and its groups.
    """

    def __init__(self, event_aggregator: EventAggregator):
        self._event_aggregator = event_aggregator

    def _create_action(self, text: str, icon_key: str) -> QAction:
        icon_path = IconPath.get_path(f"ribbon.{icon_key}")
        icon = QIcon(icon_path) if icon_path else QIcon()
        return QAction(icon, text)

    def _build_insert_tab(self, ribbon: RibbonBar) -> dict:
        layout = ribbon.add_ribbon_tab("Insert")
        actions = {}
        icon_size = QSize(24, 24)
        
        # Plots Group
        plots_group = ribbon.add_group(layout, "Plots")
        actions['insert_line_action'] = self._create_action("Line", "insert.plots.line")
        actions['insert_scatter_action'] = self._create_action("Scatter", "insert.plots.scatter")
        actions['insert_bar_action'] = self._create_action("Bar", "insert.plots.bar")
        actions['insert_area_action'] = self._create_action("Area", "insert.plots.area")
        actions['insert_pie_action'] = self._create_action("Pie", "insert.plots.pie")
        actions['insert_histogram_action'] = self._create_action("Histogram", "insert.plots.histogram")
        actions['insert_candlestick_action'] = self._create_action("Candlestick", "insert.plots.candlestick")
        actions['insert_contour_action'] = self._create_action("Contour", "insert.plots.contour")
        actions['insert_waterfall_action'] = self._create_action("Waterfall", "insert.plots.waterfall")
        actions['insert_stairs_action'] = self._create_action("Stairs", "insert.plots.stairs")
        
        for k in ['insert_line_action', 'insert_scatter_action', 'insert_bar_action', 'insert_area_action', 'insert_pie_action', 'insert_histogram_action', 'insert_candlestick_action', 'insert_contour_action', 'insert_waterfall_action', 'insert_stairs_action']:
            plots_group.add_action(actions[k], icon_size)

        # Shapes Group
        shapes_group = ribbon.add_group(layout, "Shapes")
        actions['insert_square_action'] = self._create_action("Square", "insert.shapes.square")
        actions['insert_rectangle_action'] = self._create_action("Rectangle", "insert.shapes.rectangle")
        actions['insert_circle_action'] = self._create_action("Circle", "insert.shapes.circle")
        actions['insert_pentagon_action'] = self._create_action("Pentagon", "insert.shapes.pentagon")
        actions['insert_hexagon_action'] = self._create_action("Hexagon", "insert.shapes.hexagon")
        
        for k in ['insert_square_action', 'insert_rectangle_action', 'insert_circle_action', 'insert_pentagon_action', 'insert_hexagon_action']:
            shapes_group.add_action(actions[k], icon_size)

        # Text Group
        text_group = ribbon.add_group(layout, "Text")
        actions['insert_text_field_action'] = self._create_action("Text Field", "insert.text.text_field")
        actions['insert_text_action'] = self._create_action("Text", "insert.text.text")
        actions['insert_bullet_list_action'] = self._create_action("Bullets", "insert.text.bullet_list")
        actions['insert_numbered_list_action'] = self._create_action("Numbers", "insert.text.numbered_list")
        actions['insert_check_list_action'] = self._create_action("Checklist", "insert.text.check_list")
        
        for k in ['insert_text_field_action', 'insert_text_action', 'insert_bullet_list_action', 'insert_numbered_list_action', 'insert_check_list_action']:
            text_group.add_action(actions[k], icon_size)

        # Arrows Group
        arrows_group = ribbon.add_group(layout, "Arrows")
        actions['insert_arrow_right_action'] = self._create_action("Arrow R", "insert.arrows.arrow_right")
        actions['insert_arrow_bottom_right_action'] = self._create_action("Arrow BR", "insert.arrows.arrow_bottom_right")
        
        for k in ['insert_arrow_right_action', 'insert_arrow_bottom_right_action']:
            arrows_group.add_action(actions[k], icon_size)

        # Symbols Group
        symbols_group = ribbon.add_group(layout, "Symbols")
        actions['insert_symbol_action'] = self._create_action("Symbol", "insert.symbol")
        actions['insert_formula_action'] = self._create_action("Formula", "insert.formula")
        
        for k in ['insert_symbol_action', 'insert_formula_action']:
            symbols_group.add_action(actions[k], icon_size)

        return actions

    def _build_design_tab(self, ribbon: RibbonBar) -> dict:
        layout = ribbon.add_ribbon_tab("Design")
        actions = {}
        icon_size = QSize(32, 32)
        
        # Designs Group
        designs_group = ribbon.add_group(layout, "Designs")
        actions['design_nature_action'] = self._create_action("Nature", "design.nature")
        actions['design_science_action'] = self._create_action("Science", "design.science")
        actions['design_cell_action'] = self._create_action("Cell", "design.cell")
        
        for k in ['design_nature_action', 'design_science_action', 'design_cell_action']:
            designs_group.add_action(actions[k], icon_size)

        # Variants Group
        variants_group = ribbon.add_group(layout, "Variants")
        actions['design_colors_action'] = self._create_action("Colors", "design.colors")
        actions['design_fonts_action'] = self._create_action("Fonts", "design.fonts")
        
        for k in ['design_colors_action', 'design_fonts_action']:
            variants_group.add_action(actions[k], icon_size)

        return actions

    def _build_layout_tab(self, ribbon: RibbonBar) -> dict:
        layout = ribbon.add_ribbon_tab("Layout")
        actions = {}
        icon_size = QSize(32, 32)
        
        # Page Setup Group
        page_setup_group = ribbon.add_group(layout, "Page Setup")
        actions['layout_margins_action'] = self._create_action("Margins", "layout.margins")
        actions['layout_format_action'] = self._create_action("Format", "layout.format")
        
        for k in ['layout_margins_action', 'layout_format_action']:
            page_setup_group.add_action(actions[k], icon_size)

        # Arrange Group
        arrange_group = ribbon.add_group(layout, "Arrange")
        actions['layout_grid_toggle_action'] = self._create_action("Grid", "properties.snap_to_grid")
        actions['layout_align_left_action'] = self._create_action("Align Left", "properties.alignment.align_horizontal_left")
        actions['layout_align_right_action'] = self._create_action("Align Right", "properties.alignment.align_horizontal_right")
        actions['layout_align_top_action'] = self._create_action("Align Top", "properties.alignment.align_vertical_top")
        actions['layout_align_bottom_action'] = self._create_action("Align Bottom", "properties.alignment.align_vertical_bottom")
        actions['layout_distribute_h_action'] = self._create_action("Dist. H", "properties.distribute.horizontal_distribute")
        actions['layout_distribute_v_action'] = self._create_action("Dist. V", "properties.distribute.vertical_distribute")
        
        for k in ['layout_grid_toggle_action', 'layout_align_left_action', 'layout_align_right_action', 'layout_align_top_action', 'layout_align_bottom_action', 'layout_distribute_h_action', 'layout_distribute_v_action']:
            arrange_group.add_action(actions[k], icon_size)

        return actions

    def build(self) -> tuple[RibbonBar, RibbonActions]:
        ribbon = RibbonBar()
        
        insert_actions = self._build_insert_tab(ribbon)
        design_actions = self._build_design_tab(ribbon)
        layout_actions = self._build_layout_tab(ribbon)
        
        all_actions = {**insert_actions, **design_actions, **layout_actions}
        ribbon_actions = RibbonActions(**all_actions)
        
        return ribbon, ribbon_actions

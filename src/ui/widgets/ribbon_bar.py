from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class RibbonGroup(QWidget):
    """
    A group within a Ribbon tab, containing actions and a group label at the bottom.
    """

    def __init__(self, name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)

        # Container for buttons
        self.buttons_container = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(2)

        # Group label at the bottom
        self.label = QLabel(name.upper())
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 9px; color: #888888; font-weight: bold;")

        self.main_layout.addWidget(self.buttons_container, 1)
        self.main_layout.addWidget(self.label)

        # Vertical separator line on the right
        self.line = QFrame()
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setStyleSheet("color: #3d3d3d;")

    def add_action(self, action, icon_size: QSize = QSize(32, 32)):
        button = QToolButton()
        button.setDefaultAction(action)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setIconSize(icon_size)
        # Removed fixed minimum width to allow shrinking
        self.buttons_layout.addWidget(button)


class RibbonBar(QTabWidget):
    """
    A Ribbon-style bar where tabs are controlled by the MenuBar.
    The tab bar itself is hidden.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setTabPosition(QTabWidget.North)
        self.setDocumentMode(True)
        self.tabBar().hide()
        
        # Set a reasonable maximum height for the ribbon
        self.setMaximumHeight(110)

    def add_ribbon_tab(self, name: str) -> QHBoxLayout:
        """
        Creates a new tab page with scroll support and returns its main layout.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        page = QWidget()
        page.setObjectName("RibbonTabPage")
        layout = QHBoxLayout(page)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)
        
        scroll.setWidget(page)
        self.addTab(scroll, name)
        return layout

    def add_group(self, tab_layout: QHBoxLayout, name: str) -> RibbonGroup:
        """
        Creates and adds a RibbonGroup to a tab layout.
        """
        group = RibbonGroup(name)
        tab_layout.addWidget(group)
        tab_layout.addWidget(group.line)
        return group

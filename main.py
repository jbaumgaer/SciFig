import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette 

from src.application_assembler import ApplicationAssembler
from src.application_components import ApplicationComponents


def setup_application() -> ApplicationComponents:
    """
    Creates and wires up all the core components of the application using ApplicationAssembler.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    assembler = ApplicationAssembler(app)
    return assembler.assemble()


def main():
    """The main entry point for the application."""
    context = setup_application()
    view = context.view
    app = context.app

    # Set up dark theme
    app.setStyle("Fusion") 
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(dark_palette)


    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
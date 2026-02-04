import sys

from PySide6.QtWidgets import QApplication

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

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
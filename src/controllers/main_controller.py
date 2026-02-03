import json
import tempfile
import zipfile
from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from src.models import ApplicationModel
from src.models.nodes import PlotNode


class MainController:
    """
    Manages application-level logic and orchestrates the other components.
    Connects main window UI actions to model-updating logic.
    """

    def __init__(self, model: ApplicationModel, view):  # view is a MainWindow
        self.model = model
        self.view = view

        # Connect UI element signals to controller slots
        self.view.new_layout_action.triggered.connect(self.create_new_layout)
        self.view.save_project_action.triggered.connect(self.save_project)

    def create_new_layout(self):
        """
        Clears the scene and populates it with new PlotNodes in a grid layout.
        """
        # The dialog implementation will be added in a future step.
        # For now, we will hardcode a 2x2 layout for demonstration.
        print("Creating a default 2x2 layout.")
        rows, cols = 2, 2

        self.model.clear_scene()

        margin, gutter = 0.1, 0.08
        plot_width = (1 - 2 * margin - (cols - 1) * gutter) / cols
        plot_height = (1 - 2 * margin - (rows - 1) * gutter) / rows

        for r in range(rows):
            for c in range(cols):
                left = margin + c * (plot_width + gutter)
                bottom = margin + (rows - 1 - r) * (plot_height + gutter)

                plot_node = PlotNode(name=f"Subplot {r*cols + c + 1}")
                plot_node.geometry = (left, bottom, plot_width, plot_height)

                # model.add_node emits the signal, so no need for an extra emit here
                self.model.add_node(plot_node)

    def save_project(self):
        """Saves the current project to a .sci file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Save Project",
            "",
            "SciFig Project (*.sci)",
        )

        if not file_path:
            return

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            data_dir = temp_dir / "data"
            data_dir.mkdir()

            # 1. Save all dataframes to parquet files
            for node in self.model.scene_root.all_descendants():
                if isinstance(node, PlotNode) and node.data is not None:
                    parquet_path = data_dir / f"{node.id}.parquet"
                    node.data.to_parquet(parquet_path)
            
            # 2. Get the model dictionary (which now contains data_path)
            project_dict = self.model.to_dict()

            # 3. Save the project dictionary to project.json
            json_path = temp_dir / "project.json"
            with open(json_path, "w") as f:
                json.dump(project_dict, f, indent=4)
            
            # 4. Zip the contents of the temporary directory
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_to_zip in temp_dir.rglob("*"):
                    zf.write(file_to_zip, file_to_zip.relative_to(temp_dir))
            
            print(f"Project saved to {file_path}")

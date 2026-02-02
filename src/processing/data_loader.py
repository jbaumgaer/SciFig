import pandas as pd
from PySide6.QtCore import QObject, Signal


class DataLoader(QObject):
    """
    A worker object that processes data in a separate thread.
    Inherits from QObject to use the signal/slot mechanism for thread-safe
    communication.
    """

    # Signal emitted when data processing is complete.
    # Emits the dataframe and the target PlotNode object.
    dataReady = Signal(object, object)

    # Signal emitted if an error occurs during processing.
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()

    def process_data(self, file_path: str, node):  # node is a PlotNode
        """
        The main data processing pipeline. This is the method that will be
        run in the background thread.
        """
        try:
            print(f"Data loader started for file: {file_path}")
            # This is the "mock pipeline". In the future, complex processing
            # can be added here.
            dataframe = pd.read_csv(file_path, sep=";")

            # Emit the signal with the result and the target node
            self.dataReady.emit(dataframe, node)
            print("Data loader finished successfully.")

        except Exception as e:
            # Emit an error signal if something goes wrong
            self.errorOccurred.emit(str(e))
            print(f"Data loader error: {e}")

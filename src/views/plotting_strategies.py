# This file will contain the strategy classes for different plot types.
from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from matplotlib.axes import Axes


class BasePlottingStrategy(ABC):
    """
    Abstract base class for a plotting strategy.
    """

    @abstractmethod
    def plot(self, ax: Axes, data: pd.DataFrame, x_column: str, y_columns: List[str]):
        """
        The main method to execute the plotting logic.

        :param ax: The Matplotlib axes to plot on.
        :param data: The DataFrame containing the data.
        :param x_column: The name of the column to use for the x-axis.
        :param y_columns: A list of column names to use for the y-axis.
        """
        pass


class LinePlotStrategy(BasePlottingStrategy):
    """
    A strategy for creating a line plot.
    """

    def plot(self, ax: Axes, data: pd.DataFrame, x_column: str, y_columns: List[str]):
        """
        Plots the data as one or more lines.
        """
        for y_col in y_columns:
            if x_column in data.columns and y_col in data.columns:
                ax.plot(data[x_column], data[y_col], label=y_col)

        if len(y_columns) > 1:
            ax.legend()


class ScatterPlotStrategy(BasePlottingStrategy):
    """
    A strategy for creating a scatter plot.
    """

    def plot(self, ax: Axes, data: pd.DataFrame, x_column: str, y_columns: List[str]):
        """
        Plots the data as one or more scatter series.
        """
        for y_col in y_columns:
            if x_column in data.columns and y_col in data.columns:
                ax.scatter(data[x_column], data[y_col], label=y_col)

        if len(y_columns) > 1:
            ax.legend()

"""Data package providing DataFrame, Series, and visualization capabilities."""

from .dataframe import DataFrame, DataFrameError, GroupBy, GroupByColumn, Series
from .visualization import Figure, Plot, VisualizationError, set_style

__version__ = "0.1.0"

__all__ = [
    "DataFrame",
    "Series",
    "GroupBy",
    "GroupByColumn",
    "DataFrameError",
    "Figure",
    "Plot",
    "VisualizationError",
    "set_style",
    "create_dataframe",
]


def create_dataframe(
    data: list[dict] | dict | list[list], columns: list[str] | None = None
) -> DataFrame:
    return DataFrame(data, columns=columns)

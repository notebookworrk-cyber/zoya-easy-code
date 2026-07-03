from .dataframe import DataFrame, Series, GroupBy, GroupByColumn, DataFrameError
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


def create_dataframe(data, columns=None) -> DataFrame:
    return DataFrame(data, columns=columns)

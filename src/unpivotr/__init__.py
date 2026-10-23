"""unpivotr: The Grammar of Non-Rectangular Spreadsheets and Observation Extraction in Python."""
from .cell import Cell, CellRange, col_to_letter, letter_to_col, parse_address
from .coercers import clean_number, clean_text, parse_date, to_slug
from .grid import Grid
from .flattener import CellContext, TableFlattener
from .behead import behead, as_cells_dataframe
from .synthesizer import synthesize_heterogeneous_workbook, verify_roundtrip
from .invertibility import (
    DataCorruptionError,
    InformationLossError,
    InvertibilityError,
    InvertibilityReport,
    InvertibilityVerifier,
    is_trivial_value,
    verify_invertibility,
)
from .converter import BaseTableConverter
from .hierarchy import HierarchyNode, parse_hierarchy_tree

__version__ = "0.3.0"

__all__ = [
    "Cell",
    "CellRange",
    "col_to_letter",
    "letter_to_col",
    "parse_address",
    "clean_number",
    "clean_text",
    "parse_date",
    "to_slug",
    "Grid",
    "CellContext",
    "TableFlattener",
    "behead",
    "as_cells_dataframe",
    "synthesize_heterogeneous_workbook",
    "verify_roundtrip",
    "DataCorruptionError",
    "InformationLossError",
    "InvertibilityError",
    "InvertibilityReport",
    "InvertibilityVerifier",
    "is_trivial_value",
    "verify_invertibility",
    "BaseTableConverter",
    "HierarchyNode",
    "parse_hierarchy_tree",
]

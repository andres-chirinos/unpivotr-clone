"""Implementación del operador direccional behead() de la Gramática de Hojas de Cálculo."""
from __future__ import annotations

from typing import Any, Literal
import pandas as pd

from .cell import Cell
from .grid import Grid

Direction = Literal["up", "left", "down", "right"]


def as_cells_dataframe(grid: Grid, drop_empty: bool = True) -> pd.DataFrame:
    """Convierte una cuadrícula en un DataFrame tabular donde cada fila representa una sola celda física."""
    records = []
    for r in range(1, grid.max_row + 1):
        for c in range(1, grid.max_col + 1):
            val = grid.cell_value(r, c)
            if drop_empty and (val is None or str(val).strip() == ""):
                continue
            records.append({
                "row": r,
                "col": c,
                "val": val,
                "sheet": grid.sheet_name
            })
    return pd.DataFrame(records)


def behead(
    df: pd.DataFrame,
    direction: Direction,
    name: str,
    drop_empty: bool = True,
) -> pd.DataFrame:
    """Desprende una fila o columna de cabecera en la dirección indicada y la asocia como atributo a las celdas de datos restantes.

    Direcciones:
    - 'up': Toma la fila superior como cabeceras de columna (asociadas a celdas debajo en la misma columna).
    - 'left': Toma la columna izquierda como cabeceras de fila (asociadas a celdas a la derecha en la misma fila).
    """
    if df.empty:
        return df.copy()

    df_res = df.copy()

    if direction == "up":
        # La fila mínima es la cabecera superior
        min_row = df_res["row"].min()
        header_cells = df_res[df_res["row"] == min_row][["col", "val"]].rename(columns={"val": name})
        data_cells = df_res[df_res["row"] > min_row]

        # Merge por columna
        merged = data_cells.merge(header_cells, on="col", how="left")
        return merged

    elif direction == "left":
        # La columna mínima es la cabecera izquierda
        min_col = df_res["col"].min()
        header_cells = df_res[df_res["col"] == min_col][["row", "val"]].rename(columns={"val": name})
        data_cells = df_res[df_res["col"] > min_col]

        # Merge por fila
        merged = data_cells.merge(header_cells, on="row", how="left")
        return merged

    else:
        raise NotImplementedError(f"Dirección {direction!r} no implementada aún.")

"""Verificación genérica de invertibilidad y auditoría de no-pérdida de información.

Provee herramientas matemáticas para comprobar que un proceso de des-pivoteo
o aplanado tabular preserva el 100% de la información de la hoja de cálculo
original y que la función de extracción es biyectiva/invertible.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .cell import Cell
from .coercers import clean_number
from .grid import Grid
from .flattener import CellContext


class InvertibilityError(ValueError):
    """Excepción lanzada cuando una extracción pierde información o no es invertible."""
    pass


@dataclass(frozen=True)
class InvertibilityReport:
    """Reporte formal de la verificación de invertibilidad."""
    is_invertible: bool
    total_source_cells: int
    total_extracted_observations: int
    cell_coverage_pct: float
    lost_cells_count: int
    lost_cells: list[dict[str, Any]] = field(default_factory=list)
    spurious_cells_count: int = 0
    spurious_cells: list[dict[str, Any]] = field(default_factory=list)
    mismatched_cells_count: int = 0
    mismatches: list[dict[str, Any]] = field(default_factory=list)
    max_absolute_error: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_invertible": bool(self.is_invertible),
            "total_source_cells": int(self.total_source_cells),
            "total_extracted_observations": int(self.total_extracted_observations),
            "cell_coverage_pct": float(self.cell_coverage_pct),
            "lost_cells_count": int(self.lost_cells_count),
            "spurious_cells_count": int(self.spurious_cells_count),
            "mismatched_cells_count": int(self.mismatched_cells_count),
            "max_absolute_error": float(self.max_absolute_error),
            "summary": self.summary,
            "lost_cells_sample": self.lost_cells[:10],
            "mismatches_sample": self.mismatches[:10],
        }

    def assert_valid(self) -> None:
        """Lanza InvertibilityError si se detectó pérdida de información o discrepancias."""
        if not self.is_invertible:
            raise InvertibilityError(
                f"Fallo en verificación de invertibilidad: "
                f"celdas_perdidas={self.lost_cells_count}, "
                f"discrepancias={self.mismatched_cells_count}, "
                f"cobertura={self.cell_coverage_pct:.2f}%. Detalle: {self.summary}"
            )


class InvertibilityVerifier:
    """Verificador agnóstico de fidelidad e invertibilidad de matrices tabulares."""

    def __init__(self, tolerance: float = 1e-5) -> None:
        self.tolerance = tolerance

    def verify_grids(
        self,
        source_grid: Grid,
        reconstructed_grid: Grid,
        row_start: int = 1,
        col_start: int = 1,
        row_end: int | None = None,
        col_end: int | None = None,
        cell_filter: Callable[[Cell], bool] | None = None,
    ) -> InvertibilityReport:
        """Compara celda a celda una malla original contra una malla reconstruida."""
        max_r = min(source_grid.max_row, row_end) if row_end is not None else source_grid.max_row
        max_c = min(source_grid.max_col, col_end) if col_end is not None else source_grid.max_col

        total_source_cells = 0
        total_recon_cells = 0
        lost_cells = []
        spurious_cells = []
        mismatches = []
        max_abs_err = 0.0

        for r in range(row_start, max_r + 1):
            for c in range(col_start, max_c + 1):
                src_cell = source_grid.cell(r, c)
                if cell_filter is not None and not cell_filter(src_cell):
                    continue

                src_raw = src_cell.val
                src_num = clean_number(src_raw)
                recon_raw = reconstructed_grid.cell_value(r, c)
                recon_num = clean_number(recon_raw)

                if src_num is not None:
                    total_source_cells += 1

                if recon_num is not None:
                    total_recon_cells += 1

                # 1. Comprobar si celda fuente fue perdida
                if src_num is not None and recon_num is None:
                    lost_cells.append({"row": r, "col": c, "source_value": src_num})
                    continue

                # 2. Comprobar si celda reconstruida es espuria
                if src_num is None and recon_num is not None:
                    spurious_cells.append({"row": r, "col": c, "reconstructed_value": recon_num})
                    continue

                # 3. Comprobar valor si ambos existen
                if src_num is not None and recon_num is not None:
                    err = abs(src_num - recon_num)
                    if err > max_abs_err:
                        max_abs_err = err
                    if err > self.tolerance:
                        mismatches.append({
                            "row": r,
                            "col": c,
                            "source_value": src_num,
                            "reconstructed_value": recon_num,
                            "diff": err,
                        })

        coverage = (
            ((total_source_cells - len(lost_cells)) / total_source_cells * 100.0)
            if total_source_cells > 0
            else 100.0
        )
        is_invertible = (
            len(lost_cells) == 0
            and len(spurious_cells) == 0
            and len(mismatches) == 0
        )

        summary = (
            f"Invertibilidad 100% confirmada. Total celdas: {total_source_cells}, "
            f"Error máx: {max_abs_err:.6e}"
            if is_invertible
            else f"Pérdida detectada: {len(lost_cells)} celdas perdidas, "
                 f"{len(spurious_cells)} espurias, {len(mismatches)} diferencias numéricas."
        )

        return InvertibilityReport(
            is_invertible=is_invertible,
            total_source_cells=total_source_cells,
            total_extracted_observations=total_recon_cells,
            cell_coverage_pct=coverage,
            lost_cells_count=len(lost_cells),
            lost_cells=lost_cells,
            spurious_cells_count=len(spurious_cells),
            spurious_cells=spurious_cells,
            mismatched_cells_count=len(mismatches),
            mismatches=mismatches,
            max_absolute_error=max_abs_err,
            summary=summary,
        )


def verify_invertibility(
    target: Any,
    reconstructed_or_df: Any = None,
    invert_fn: Callable[[Any], Grid] | None = None,
    tolerance: float = 1e-5,
    row_start: int = 1,
    col_start: int = 1,
    row_end: int | None = None,
    col_end: int | None = None,
) -> InvertibilityReport:
    """Función de conveniencia genérica para verificar invertibilidad.

    Acepta:
    - un TableFlattener (con o sin DataFrame)
    - o (source_grid, reconstructed_grid)
    - o (source_grid, dataframe, invert_fn)
    """
    verifier = InvertibilityVerifier(tolerance=tolerance)

    # Caso 1: Se pasó un TableFlattener
    if hasattr(target, "to_dataframe") and hasattr(target, "invert"):
        flattener = target
        df = reconstructed_or_df if isinstance(reconstructed_or_df, pd.DataFrame) else flattener.to_dataframe()
        recon_grid = flattener.invert(df)
        return verifier.verify_grids(
            source_grid=flattener._grid,
            reconstructed_grid=recon_grid,
            row_start=flattener._row_start,
            col_start=flattener._col_start,
            row_end=flattener._row_end,
            col_end=flattener._col_end,
            cell_filter=lambda c: all(p(CellContext(val=clean_number(c.val), row=c.row, col=c.col, grid=flattener._grid)) for p in flattener._filters) if clean_number(c.val) is not None else True,
        )

    # Caso 2: Se pasaron dos Grids
    if isinstance(target, Grid) and isinstance(reconstructed_or_df, Grid):
        return verifier.verify_grids(
            source_grid=target,
            reconstructed_grid=reconstructed_or_df,
            row_start=row_start,
            col_start=col_start,
            row_end=row_end,
            col_end=col_end,
        )

    # Caso 3: source_grid + DataFrame + invert_fn
    if isinstance(target, Grid) and invert_fn is not None:
        recon_grid = invert_fn(reconstructed_or_df)
        return verifier.verify_grids(
            source_grid=target,
            reconstructed_grid=recon_grid,
            row_start=row_start,
            col_start=col_start,
            row_end=row_end,
            col_end=col_end,
        )

    raise TypeError(
        f"Argumentos no soportados para verify_invertibility: target={type(target)}, "
        f"reconstructed={type(reconstructed_or_df)}"
    )

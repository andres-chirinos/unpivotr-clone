"""Verificación genérica de invertibilidad, fidelidad matricial y manejo de datos triviales.

Provee herramientas matemáticas agnósticas de formato para comprobar que un proceso de
des-pivoteo preserva el 100% de la información relevante de la hoja o matriz original.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .cell import Cell
from .coercers import clean_number
from .grid import Grid


class InvertibilityError(ValueError):
    """Excepción base para fallas en la verificación de invertibilidad."""
    pass


class InformationLossError(InvertibilityError):
    """Excepción lanzada cuando se pierden observaciones o celdas no triviales."""
    pass


class DataCorruptionError(InvertibilityError):
    """Excepción lanzada cuando valores reconstruidos difieren más allá de la tolerancia."""
    pass


def is_trivial_value(val: Any) -> bool:
    """Identifica si un valor es trivial/vacío/sin información estadística relevante.

    Detecta de forma segura:
    - None, NaN, inf
    - Cadenas vacías o solo espacios
    - Guiones y líneas ('-', '--', '—', '–', '- -')
    - Marcadores estándar de no disponibilidad ('s.d.', 's/d', 'n.d.', 'n/d', 'N/A', 'NA', 'null', 'None')
    """
    if val is None:
        return True
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return True
    s = str(val).strip()
    if not s:
        return True
    s_clean = re.sub(r"\s+", "", s)
    if re.fullmatch(r"[-—–\.]+", s_clean):
        return True
    if re.fullmatch(r"(?i)s[./]?d[.]?|n[./]?d[.]?|n/?a|null|none", s_clean):
        return True
    return False


@dataclass(frozen=True)
class InvertibilityReport:
    """Reporte formal de la verificación de invertibilidad y fidelidad matricial."""
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
    trivial_cells_ignored: int = 0
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
            "trivial_cells_ignored": int(self.trivial_cells_ignored),
            "max_absolute_error": float(self.max_absolute_error),
            "summary": self.summary,
            "lost_cells_sample": self.lost_cells[:10],
            "mismatches_sample": self.mismatches[:10],
        }

    def assert_valid(self) -> None:
        """Lanza excepción especializada si la verificación falla."""
        if self.lost_cells_count > 0:
            raise InformationLossError(
                f"Pérdida de información crítica: {self.lost_cells_count} celdas de datos "
                f"no fueron capturadas en la extracción. Cobertura: {self.cell_coverage_pct:.2f}%."
            )
        if self.mismatched_cells_count > 0:
            raise DataCorruptionError(
                f"Corrupción de datos numéricos: {self.mismatched_cells_count} celdas divergen "
                f"con error máx {self.max_absolute_error:.6e}."
            )
        if not self.is_invertible:
            raise InvertibilityError(f"Fallo de invertibilidad: {self.summary}")


class InvertibilityVerifier:
    """Verificador agnóstico de fidelidad e invertibilidad de matrices tabulares."""

    def __init__(
        self,
        tolerance: float = 1e-4,
        ignore_trivial: bool = True,
        ignore_non_numeric: bool = True,
    ) -> None:
        self.tolerance = tolerance
        self.ignore_trivial = ignore_trivial
        self.ignore_non_numeric = ignore_non_numeric

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
        """Compara celda a celda dos mallas matriciales aplicando tolerancia y filtrado de datos triviales."""
        max_r = min(source_grid.max_row, row_end) if row_end is not None else source_grid.max_row
        max_c = min(source_grid.max_col, col_end) if col_end is not None else source_grid.max_col

        total_source_cells = 0
        total_recon_cells = 0
        trivial_ignored = 0
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
                recon_raw = reconstructed_grid.cell_value(r, c)

                # Tratamiento de celdas triviales
                if self.ignore_trivial and is_trivial_value(src_raw):
                    trivial_ignored += 1
                    # Si ambos son triviales o recon es trivial, no hay violación
                    if not is_trivial_value(recon_raw):
                        spurious_cells.append({"row": r, "col": c, "reconstructed_value": recon_raw})
                    continue

                src_num = clean_number(src_raw)
                recon_num = clean_number(recon_raw)

                if self.ignore_non_numeric and src_num is None:
                    # Texto explicativo, títulos o encabezados dentro del rango
                    trivial_ignored += 1
                    continue

                total_source_cells += 1
                if recon_num is not None:
                    total_recon_cells += 1

                # 1. Comprobar si celda con dato relevante fue perdida
                if src_num is not None and recon_num is None:
                    lost_cells.append({"row": r, "col": c, "source_value": src_num})
                    continue

                # 2. Comprobar discrepancia numérica
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
            f"Invertibilidad confirmada. Celdas evaluadas: {total_source_cells}, "
            f"Triviales ignoradas: {trivial_ignored}, Error máx: {max_abs_err:.6e}."
            if is_invertible
            else f"Pérdida/Error: {len(lost_cells)} perdidas, {len(spurious_cells)} espurias, "
                 f"{len(mismatches)} divergencias."
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
            trivial_cells_ignored=trivial_ignored,
            max_absolute_error=max_abs_err,
            summary=summary,
        )


def verify_invertibility(
    target: Any,
    reconstructed_or_df: Any = None,
    invert_fn: Callable[[Any], Grid] | None = None,
    tolerance: float = 1e-4,
    ignore_trivial: bool = True,
    row_start: int = 1,
    col_start: int = 1,
    row_end: int | None = None,
    col_end: int | None = None,
) -> InvertibilityReport:
    """Función universal y agnóstica de formato para verificar invertibilidad matricial.

    Formatos aceptados como target y reconstrucción:
    - TableFlattener (con o sin DataFrame)
    - BaseTableConverter (con o sin DataFrame o dict)
    - Grid, openpyxl Worksheet/Workbook
    - pandas DataFrame (en formato matriz wide o tidy long con _row/_col)
    - numpy ndarray, list[list[Any]]
    - Path / str a archivo Excel
    """
    from .flattener import CellContext, TableFlattener

    verifier = InvertibilityVerifier(tolerance=tolerance, ignore_trivial=ignore_trivial)

    # Caso 1: TableFlattener
    if isinstance(target, TableFlattener) or (hasattr(target, "to_dataframe") and hasattr(target, "invert")):
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
            cell_filter=lambda c: all(
                p(CellContext(val=clean_number(c.val), row=c.row, col=c.col, grid=flattener._grid))
                for p in flattener._filters
            ) if clean_number(c.val) is not None else True,
        )

    # Caso 2: Conversor con last_flattener
    if hasattr(target, "last_flattener") and target.last_flattener is not None:
        return verify_invertibility(
            target.last_flattener,
            reconstructed_or_df=reconstructed_or_df,
            tolerance=tolerance,
            ignore_trivial=ignore_trivial,
        )

    # Caso 3: Invert_fn provisto
    if invert_fn is not None:
        source_grid = Grid.from_any(target)
        recon_grid = invert_fn(reconstructed_or_df)
        return verifier.verify_grids(
            source_grid=source_grid,
            reconstructed_grid=recon_grid,
            row_start=row_start,
            col_start=col_start,
            row_end=row_end,
            col_end=col_end,
        )

    # Caso 4: Conversión agnóstica de matrices (Grid, ndarray, list of lists, DataFrame, etc.)
    source_grid = Grid.from_any(target)
    recon_grid = Grid.from_any(reconstructed_or_df)
    return verifier.verify_grids(
        source_grid=source_grid,
        reconstructed_grid=recon_grid,
        row_start=row_start,
        col_start=col_start,
        row_end=row_end,
        col_end=col_end,
    )

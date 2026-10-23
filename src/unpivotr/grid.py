"""Malla bidimensional indexada con soporte de propagación espacial."""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .cell import Cell, parse_address


class Grid:
    """Representa una hoja de cálculo bidimensional con acceso O(1) y propagación."""

    def __init__(
        self,
        rows: list[list[Any] | tuple[Any, ...]],
        sheet_name: str = "Sheet1",
    ) -> None:
        self.sheet_name = sheet_name
        self._rows: list[tuple[Any, ...]] = [tuple(r) for r in rows]
        self.max_row = len(self._rows)
        self.max_col = max((len(r) for r in self._rows), default=0)

    @classmethod
    def empty(cls, max_row: int = 0, max_col: int = 0, sheet_name: str = "Sheet1") -> Grid:
        """Crea una malla vacía inicializada con dimensiones opcionales."""
        rows = [[None] * max_col for _ in range(max_row)]
        return cls(rows, sheet_name=sheet_name)

    @classmethod
    def from_rows(cls, rows: list[list[Any] | tuple[Any, ...]], sheet_name: str = "Sheet1") -> Grid:
        """Crea una malla a partir de una lista de filas en memoria."""
        return cls(rows, sheet_name=sheet_name)

    @classmethod
    def from_worksheet(cls, ws: Any) -> Grid:
        """Crea una malla leyendo valores desde un Worksheet de openpyxl."""
        sheet_name = getattr(ws, "title", "Sheet1")
        rows = list(ws.iter_rows(values_only=True))
        return cls(rows, sheet_name=sheet_name)

    @classmethod
    def from_excel(cls, file_path: str | Path, sheet_name: str | None = None) -> Grid:
        """Carga un archivo Excel (.xlsx) directamente en memoria."""
        import openpyxl

        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        try:
            ws = wb[sheet_name] if sheet_name else wb.active
            return cls.from_worksheet(ws)
        finally:
            wb.close()

    def cell_value(self, r: int, c: int) -> Any:
        """Obtiene el valor crudo en la fila r y columna c (base 1)."""
        if 1 <= r <= self.max_row:
            row_tuple = self._rows[r - 1]
            if 1 <= c <= len(row_tuple):
                return row_tuple[c - 1]
        return None

    def cell(self, r: int, c: int) -> Cell:
        """Obtiene un objeto Cell fuertemente tipado en (r, c)."""
        return Cell(row=r, col=c, val=self.cell_value(r, c), sheet=self.sheet_name)

    def set_cell(self, r: int, c: int, val: Any) -> None:
        """Asigna un valor en la fila r y columna c (base 1), expandiendo la matriz si es necesario."""
        while len(self._rows) < r:
            self._rows.append(tuple())
        current_row = list(self._rows[r - 1])
        while len(current_row) < c:
            current_row.append(None)
        current_row[c - 1] = val
        self._rows[r - 1] = tuple(current_row)
        self.max_row = max(self.max_row, r)
        self.max_col = max(self.max_col, len(current_row))

    def clone(self) -> Grid:
        """Crea una copia profunda en memoria de la malla actual."""
        rows_copy = [list(r) for r in self._rows]
        return Grid(rows_copy, sheet_name=self.sheet_name)

    def to_rows(self) -> list[list[Any]]:
        """Exporta la malla como una lista de listas modificable."""
        return [list(r) for r in self._rows]

    def to_worksheet(self, ws: Any) -> None:
        """Escribe el contenido completo de la malla en una hoja openpyxl."""
        for r_idx, row in enumerate(self._rows, start=1):
            for c_idx, val in enumerate(row, start=1):
                if val is not None:
                    ws.cell(row=r_idx, column=c_idx, value=val)

    def to_excel(self, file_path: str | Path) -> None:
        """Guarda la malla directamente en un archivo Excel (.xlsx)."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.sheet_name
        self.to_worksheet(ws)
        wb.save(file_path)

    def __getitem__(self, item: tuple[int, int] | str) -> Cell:
        if isinstance(item, str):
            r, c = parse_address(item)
            return self.cell(r, c)
        r, c = item
        return self.cell(r, c)

    def row_ffill(self, r: int, c: int) -> Any:
        """Busca hacia la izquierda en la fila r el primer valor no vacío (resuelve celdas combinadas)."""
        for col_idx in range(c, 0, -1):
            v = self.cell_value(r, col_idx)
            if v is not None and str(v).strip() != "":
                return v
        return None

    def col_ffill(self, r: int, c: int) -> Any:
        """Busca hacia arriba en la columna c el primer valor no vacío (resuelve jerarquías de fila)."""
        for row_idx in range(r, 0, -1):
            v = self.cell_value(row_idx, c)
            if v is not None and str(v).strip() != "":
                return v
        return None

    def find_anchor(self, pattern: str, cell_address: str | None = None) -> Cell | None:
        """Verifica o localiza una celda ancla cuyo contenido coincide con una expresión regular."""
        rx = re.compile(pattern, re.IGNORECASE)

        if cell_address:
            r, c = parse_address(cell_address)
            val = str(self.cell_value(r, c) or "").strip()
            if rx.search(val):
                return self.cell(r, c)
            return None

        # Si no se especificó celda, buscar en las primeras 25 filas y 15 columnas
        for r in range(1, min(self.max_row + 1, 25)):
            for c in range(1, min(self.max_col + 1, 15)):
                val = str(self.cell_value(r, c) or "").strip()
                if rx.search(val):
                    return self.cell(r, c)
        return None

    def iter_cells(
        self,
        row_start: int = 1,
        col_start: int = 1,
        row_end: int | None = None,
        col_end: int | None = None,
    ) -> Iterator[Cell]:
        """Itera sobre un rango rectangular de celdas en orden fila-columna."""
        max_r = min(self.max_row, row_end) if row_end is not None else self.max_row
        max_c = min(self.max_col, col_end) if col_end is not None else self.max_col

        for r in range(row_start, max_r + 1):
            for c in range(col_start, max_c + 1):
                yield self.cell(r, c)

"""Motor fluído para transformar hojas de cálculo en observaciones relacionales."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .cell import Cell, parse_address
from .coercers import clean_number, parse_date, to_slug
from .grid import Grid


@dataclass(frozen=True, slots=True)
class CellContext:
    """Contexto dinámico inyectado en cada celda que contiene una medida u observación."""
    val: Any
    row: int
    col: int
    grid: Grid

    def cell(self, r: int, c: int) -> Cell:
        return self.grid.cell(r, c)

    def row_val(self, r: int) -> Any:
        """Valor en la fila 'r' y la misma columna que la celda actual."""
        return self.grid.cell_value(r, self.col)

    def col_val(self, c: int) -> Any:
        """Valor en la columna 'c' y la misma fila que la celda actual."""
        return self.grid.cell_value(self.row, c)

    def row_ffill(self, r: int) -> Any:
        """Cabecera en fila 'r' propagada horizontalmente (resuelve celdas combinadas)."""
        return self.grid.row_ffill(r, self.col)

    def col_ffill(self, c: int) -> Any:
        """Cabecera en columna 'c' propagada verticalmente hacia arriba."""
        return self.grid.col_ffill(self.row, c)

    def offset(self, dr: int, dc: int) -> Any:
        """Valor con desplazamiento relativo (row + dr, col + dc)."""
        return self.grid.cell_value(self.row + dr, self.col + dc)

    @property
    def sheet_name(self) -> str:
        return self.grid.sheet_name

    @property
    def slug(self) -> str:
        return to_slug(self.val)


class TableFlattener:
    """Fluent Builder para aplanar tablas complejas con lógica expresada en código e inversión biyectiva."""

    def __init__(self, table_id: str = "table") -> None:
        self.table_id = table_id
        self._grid: Grid | None = None
        self._anchor_cell: str | None = None
        self._anchor_pattern: str | None = None
        self._row_start = 1
        self._col_start = 1
        self._row_end: int | None = None
        self._col_end: int | None = None
        self._bindings: dict[str, Callable[[CellContext], Any]] = {}
        self._filters: list[Callable[[CellContext], bool]] = []
        self._value_transform: Callable[[float], float] = lambda v: v
        self._coordinate_map: dict[tuple[str, str], tuple[int, int]] = {}
        self._cell_coords: list[tuple[int, int]] = []

    def from_grid(self, grid: Grid) -> TableFlattener:
        self._grid = grid
        return self

    def from_file(self, file_path: str | Path, sheet_name: str | None = None) -> TableFlattener:
        self._grid = Grid.from_excel(file_path, sheet_name=sheet_name)
        return self

    def from_sheet(self, ws: Any) -> TableFlattener:
        self._grid = Grid.from_worksheet(ws)
        return self

    def validate_anchor(self, cell: str, pattern: str) -> TableFlattener:
        """Verifica que la celda ancla cumpla la expresión regular requerida."""
        self._anchor_cell = cell
        self._anchor_pattern = pattern
        return self

    def data_bounds(
        self,
        row_start: int,
        col_start: int,
        row_end: int | None = None,
        col_end: int | None = None,
    ) -> TableFlattener:
        """Delimita el rango bidimensional que contiene las medidas de observación."""
        self._row_start = row_start
        self._col_start = col_start
        self._row_end = row_end
        self._col_end = col_end
        return self

    def bind(self, field_name: str, resolver: Callable[[CellContext], Any] | Any) -> TableFlattener:
        """Asocia un campo a un lambda (ctx -> valor) o a un valor constante."""
        if callable(resolver):
            self._bindings[field_name] = resolver
        else:
            self._bindings[field_name] = lambda ctx, val=resolver: val
        return self

    def bind_date(
        self,
        resolver: Callable[[CellContext], Any] | int,
        default_year: int | None = None,
    ) -> TableFlattener:
        """Helper para asociar la fecha: si es entero H, lee de la fila H en misma columna."""
        if isinstance(resolver, int):
            row_idx = resolver
            fn = lambda ctx: parse_date(ctx.row_val(row_idx), default_year=default_year)
        else:
            fn = lambda ctx: parse_date(resolver(ctx), default_year=default_year)
        return self.bind("fecha", fn)

    def bind_id(self, resolver: Callable[[CellContext], Any] | int) -> TableFlattener:
        """Helper para el identificador de serie: si es entero K, lee de columna K."""
        if isinstance(resolver, int):
            col_idx = resolver
            fn = lambda ctx: f"{self.table_id}_{to_slug(ctx.col_val(col_idx))}"
        else:
            fn = resolver
        return self.bind("id", fn)

    def transform_value(self, fn: Callable[[float], float]) -> TableFlattener:
        """Aplica una transformación o conversión de unidades al valor extraído."""
        self._value_transform = fn
        return self

    def filter(self, predicate: Callable[[CellContext], bool]) -> TableFlattener:
        """Filtro de nivel de celda. Si retorna False, la observación se descarta."""
        self._filters.append(predicate)
        return self

    @property
    def coordinate_map(self) -> dict[tuple[str, str], tuple[int, int]]:
        """Mapeo inverso biyectivo: (id, fecha) -> (row, col)."""
        return dict(self._coordinate_map)

    def to_records(self, include_coords: bool = False) -> list[dict[str, Any]]:
        """Extrae la lista de observaciones normalizadas conforme a las reglas configuradas."""
        if not self._grid:
            raise ValueError(f"No se ha cargado una cuadrícula para la tabla '{self.table_id}'.")

        # 1. Validación de celda ancla
        if self._anchor_cell and self._anchor_pattern:
            anchor = self._grid.find_anchor(self._anchor_pattern, self._anchor_cell)
            if not anchor:
                r, c = parse_address(self._anchor_cell)
                actual_val = self._grid.cell_value(r, c)
                raise ValueError(
                    f"Estructura modificada en '{self.table_id}': Celda ancla {self._anchor_cell} "
                    f"con valor {actual_val!r} no coincide con patrón '{self._anchor_pattern}'."
                )

        max_r = min(self._grid.max_row, self._row_end) if self._row_end is not None else self._grid.max_row
        max_c = min(self._grid.max_col, self._col_end) if self._col_end is not None else self._grid.max_col

        observations: list[dict[str, Any]] = []
        self._coordinate_map.clear()
        self._cell_coords.clear()

        # 2. Iteración cartesiana sobre el rango de datos
        for r in range(self._row_start, max_r + 1):
            for c in range(self._col_start, max_c + 1):
                raw_cell_val = self._grid.cell_value(r, c)
                num_val = clean_number(raw_cell_val)
                if num_val is None:
                    continue

                ctx = CellContext(val=num_val, row=r, col=c, grid=self._grid)

                # Aplicar predicados de filtrado
                if not all(p(ctx) for p in self._filters):
                    continue

                final_value = self._value_transform(num_val)

                # Construir el registro
                record: dict[str, Any] = {"valor": final_value}
                for f_name, resolver in self._bindings.items():
                    record[f_name] = resolver(ctx)

                # Garantizar campos mínimos indispensables
                if record.get("id") and record.get("fecha"):
                    key = (str(record["id"]), str(record["fecha"]))
                    self._coordinate_map[key] = (r, c)
                    self._cell_coords.append((r, c))

                    if include_coords:
                        record["_row"] = r
                        record["_col"] = c

                    observations.append(record)

        return observations

    def to_dataframe(self, include_coords: bool = False) -> pd.DataFrame:
        """Convierte las observaciones extraídas a un DataFrame de pandas deduplicado."""
        records = self.to_records(include_coords=include_coords)
        if not records:
            cols = ["id", "fecha", "categoria", "valor", "unidad", "descripcion"]
            if include_coords:
                cols.extend(["_row", "_col"])
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(records)
        if "id" in df.columns and "fecha" in df.columns:
            df = df.drop_duplicates(subset=["id", "fecha"], keep="last")
        return df

    def invert(
        self,
        data: pd.DataFrame | list[dict[str, Any]],
        preserve_headers: bool = True,
    ) -> Grid:
        """Inversión biyectiva: reconstruye la malla Grid original a partir de las observaciones tidy.

        Si preserve_headers=True, clona los metadatos y encabezados originales de la hoja
        y rellena las celdas de datos con los valores exactos del DataFrame.
        """
        if self._grid is None:
            raise ValueError("No hay cuadrícula base para calcular la inversión.")

        # Asegurar que el mapa de coordenadas esté poblado
        if not self._coordinate_map:
            self.to_records()

        if preserve_headers:
            recon = self._grid.clone()
            # Limpiar todas las celdas en la zona de observaciones para que solo contengan lo extraído
            for r in range(self._row_start, self._grid.max_row + 1):
                for c in range(self._col_start, self._grid.max_col + 1):
                    recon.set_cell(r, c, None)
        else:
            recon = Grid.empty(self._grid.max_row, self._grid.max_col, self._grid.sheet_name)

        records = data.to_dict(orient="records") if isinstance(data, pd.DataFrame) else data

        for row in records:
            val = row.get("valor")
            if val is None or pd.isna(val):
                continue

            r, c = None, None
            if "_row" in row and "_col" in row:
                r, c = int(row["_row"]), int(row["_col"])
            else:
                key = (str(row.get("id")), str(row.get("fecha")))
                coords = self._coordinate_map.get(key)
                if coords:
                    r, c = coords

            if r is not None and c is not None:
                recon.set_cell(r, c, float(val))

        return recon

    def verify_invertibility(
        self,
        df: pd.DataFrame | None = None,
        tolerance: float = 1e-5,
    ) -> Any:
        """Ejecuta una auditoría matemática de invertibilidad y no pérdida de información."""
        from .invertibility import verify_invertibility

        return verify_invertibility(self, reconstructed_or_df=df, tolerance=tolerance)

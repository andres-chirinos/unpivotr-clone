"""Modelado espacial de celdas individuales y rangos rectangulares."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def col_to_letter(col_idx: int) -> str:
    """Convierte un índice de columna 1-based (ej. 1, 27) a letras Excel (ej. 'A', 'AA')."""
    if col_idx < 1:
        raise ValueError(f"Índice de columna inválido: {col_idx}. Debe ser >= 1.")
    result = []
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))


def letter_to_col(letters: str) -> int:
    """Convierte letras de columna Excel (ej. 'A', 'BC') a índice 1-based (ej. 1, 55)."""
    clean = letters.strip().upper()
    if not clean.isalpha():
        raise ValueError(f"Letras de columna inválidas: {letters!r}")
    idx = 0
    for ch in clean:
        idx = idx * 26 + (ord(ch) - 64)
    return idx


def parse_address(addr: str) -> tuple[int, int]:
    """Convierte una dirección A1 (ej. 'B12') en tupla (row, col) con base 1."""
    m = re.match(r"^([A-Za-z]+)(\d+)$", addr.strip())
    if not m:
        raise ValueError(f"Dirección de celda Excel inválida: {addr!r}")
    col_str, row_str = m.groups()
    return int(row_str), letter_to_col(col_str)


@dataclass(frozen=True, slots=True)
class Cell:
    """Representa una celda individual en una hoja de cálculo con posición y valor."""
    row: int
    col: int
    val: Any
    sheet: str = "Sheet1"

    @property
    def address(self) -> str:
        """Dirección en notación clásica de Excel, ej. 'B5'."""
        return f"{col_to_letter(self.col)}{self.row}"

    @property
    def is_empty(self) -> bool:
        """Determina si la celda no contiene datos significativos."""
        if self.val is None:
            return True
        s = str(self.val).strip()
        return s in ("", "-", "n/d", "N/D", "NaN", "nan", "null", "NULL")

    def __repr__(self) -> str:
        return f"Cell({self.address}={self.val!r})"


@dataclass(frozen=True, slots=True)
class CellRange:
    """Rango rectangular bidimensional en una cuadrícula de hoja de cálculo."""
    row_start: int
    col_start: int
    row_end: int | None = None
    col_end: int | None = None

    @classmethod
    def from_a1(cls, range_str: str) -> CellRange:
        """Construye un rango a partir de notación A1 (ej. 'B5:Z100' o 'A1')."""
        parts = range_str.split(":")
        r1, c1 = parse_address(parts[0])
        if len(parts) == 1:
            return cls(row_start=r1, col_start=c1, row_end=r1, col_end=c1)
        r2, c2 = parse_address(parts[1])
        return cls(
            row_start=min(r1, r2),
            col_start=min(c1, c2),
            row_end=max(r1, r2),
            col_end=max(c1, c2),
        )

    def contains(self, r: int, c: int) -> bool:
        if r < self.row_start or c < self.col_start:
            return False
        if self.row_end is not None and r > self.row_end:
            return False
        if self.col_end is not None and c > self.col_end:
            return False
        return True

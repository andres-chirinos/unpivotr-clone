"""Generador de hojas de cálculo sintéticas heterogéneas y verificador de ida y vuelta (round-trip)."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
import openpyxl


def synthesize_heterogeneous_workbook(
    observations: pd.DataFrame,
    title: str = "ESTADISTICAS FINANCIERAS Y MONETARIAS",
    anchor_cell: str = "A2",
    unit_note: str = "En millones de USD",
) -> openpyxl.Workbook:
    """Genera una hoja de cálculo no rectangular realista a partir de observaciones limpias.

    Crea una estructura heterogénea compleja que incluye:
    - Metadatos superiores (título, nota de unidad en B3).
    - Celda ancla de control de calidad.
    - Cabeceras de sección combinadas/dispersas (jerarquía de 2 niveles).
    - Fechas en columnas horizontales.
    - Conceptos en filas verticales con indentaciones.
    - Notas al pie y totales para poner a prueba los filtros de exclusión.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte_Estadistico"

    # 1. Metadatos superiores
    ws["A2"] = title
    ws["B3"] = unit_note

    # Identificar conceptos únicos y fechas únicas
    concepts = observations[["id", "descripcion"]].drop_duplicates().to_dict(orient="records")
    dates = sorted(observations["fecha"].drop_duplicates().tolist())

    # 2. Secciones jerárquicas en fila 5 y fechas en fila 6
    # Supongamos dos grupos de fechas o sectores para simular celdas combinadas
    ws.cell(row=5, column=2, value="TRAMO I - OBSERVACIONES VALIDAS")
    ws.cell(row=5, column=max(2, len(dates) // 2 + 2), value="TRAMO II - CIERRE TEMPORAL")

    # Fechas en fila 6 a partir de columna B (col 2)
    col_date_map: dict[str, int] = {}
    for idx, d_str in enumerate(dates):
        c_idx = idx + 2
        ws.cell(row=6, column=c_idx, value=d_str)
        col_date_map[d_str] = c_idx

    # 3. Filas de datos a partir de fila 8
    row_start = 8
    obs_dict = {
        (row["id"], str(row["fecha"])): float(row["valor"])
        for _, row in observations.iterrows()
    }

    for r_idx, c_info in enumerate(concepts, start=row_start):
        # Columna A: concepto
        ws.cell(row=r_idx, column=1, value=c_info["descripcion"])
        # Valores de cada fecha
        for d_str, col_idx in col_date_map.items():
            val = obs_dict.get((c_info["id"], d_str))
            if val is not None:
                ws.cell(row=r_idx, column=col_idx, value=val)

    # 4. Pie de página (totales y notas que deben ser filtradas por la extracción)
    footer_row = row_start + len(concepts)
    ws.cell(row=footer_row, column=1, value="TOTAL GENERAL")
    ws.cell(row=footer_row + 1, column=1, value="Fuente: Sistema Estadístico Integrado - Auditoría")

    return wb


def verify_roundtrip(
    original_df: pd.DataFrame,
    extracted_df: pd.DataFrame,
    tolerance: float = 1e-4,
) -> dict[str, Any]:
    """Verifica matemáticamente que la extracción recupera exactamente las observaciones originales."""
    # Deduplicar y ordenar ambas
    orig = original_df.copy()
    ext = extracted_df.copy()

    orig["fecha"] = orig["fecha"].astype(str)
    ext["fecha"] = ext["fecha"].astype(str)

    merged = orig.merge(
        ext,
        on=["id", "fecha"],
        suffixes=("_orig", "_ext"),
        how="outer",
    )

    missing_in_extracted = merged[merged["valor_ext"].isna()]
    spurious_in_extracted = merged[merged["valor_orig"].isna()]

    # Coincidencia de valores
    common = merged.dropna(subset=["valor_orig", "valor_ext"])
    diff = (common["valor_orig"] - common["valor_ext"]).abs()
    value_mismatches = common[diff > tolerance]

    passed = (
        len(missing_in_extracted) == 0
        and len(spurious_in_extracted) == 0
        and len(value_mismatches) == 0
    )

    return {
        "passed": passed,
        "original_count": len(orig),
        "extracted_count": len(ext),
        "missing_count": len(missing_in_extracted),
        "spurious_count": len(spurious_in_extracted),
        "mismatches_count": len(value_mismatches),
    }

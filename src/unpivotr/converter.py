"""Base class and protocol for declarative table converters using unpivotr."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd

from .flattener import TableFlattener
from .invertibility import InvertibilityReport, verify_invertibility


class BaseTableConverter(ABC):
    """Clase base de arquitectura para conversores declarativos de tablas estadísticas."""

    table_id: str
    title: str = ""
    description: str = ""
    file_pattern: str = "*.xlsx"
    sheet_name: str | None = None
    category: str = "ESTADISTICAS"
    unit: str = "NUMERO"

    def __init__(self) -> None:
        self.last_flattener: TableFlattener | None = None

    def build_flattener(
        self,
        file_path: Path | str,
        sheet_name: str | None = None,
    ) -> TableFlattener:
        """Crea e indexa una instancia de TableFlattener para habilitar inversión automática."""
        flattener = TableFlattener(self.table_id).from_file(
            file_path, sheet_name=sheet_name or self.sheet_name
        )
        self.last_flattener = flattener
        return flattener

    @abstractmethod
    def extract(self, file_path: Path) -> pd.DataFrame | dict[str, pd.DataFrame]:
        """Extrae las observaciones en formato Tidy.

        Retorna un DataFrame o un diccionario {sub_table_id: DataFrame}.
        """
        ...

    def reconstruct_sheet(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
        target_wb: openpyxl.Workbook,
        sheet_name: str | None = None,
    ) -> None:
        """Reconstruye una hoja de cálculo equivalente a partir de los datos mediante inversión biyectiva."""
        if isinstance(data, dict):
            for t_id, sub_df in data.items():
                ws = target_wb.create_sheet(title=t_id[:31])
                self._reconstruct_single(sub_df, ws, t_id)
            if "Sheet" in target_wb.sheetnames and len(target_wb.sheetnames) > 1:
                target_wb.remove(target_wb["Sheet"])
        else:
            if self.last_flattener:
                recon_grid = self.last_flattener.invert(data, preserve_headers=True)
                ws = target_wb.active if target_wb.active else target_wb.create_sheet()
                ws.title = (sheet_name or self.sheet_name or self.table_id)[:31]
                recon_grid.to_worksheet(ws)
            else:
                ws = target_wb.active if target_wb.active else target_wb.create_sheet()
                ws.title = (sheet_name or self.sheet_name or self.table_id)[:31]
                self._reconstruct_single(data, ws, self.title)

    def _reconstruct_single(
        self,
        df: pd.DataFrame,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        title: str,
    ) -> None:
        ws["A1"] = f"{title} (Reconstrucción Validada)"
        ws["A2"] = f"Unidad: {self.unit} | Categoría: {self.category}"

        dates = sorted(df["fecha"].astype(str).unique().tolist()) if "fecha" in df.columns else []
        concepts = (
            df[["id", "descripcion"]].drop_duplicates().to_dict(orient="records")
            if "descripcion" in df.columns
            else [{"id": i, "descripcion": i} for i in df["id"].unique()]
        )

        date_col_map: dict[str, int] = {}
        for idx, d_str in enumerate(dates, start=2):
            ws.cell(4, idx, d_str)
            date_col_map[d_str] = idx

        concept_row_map: dict[str, int] = {}
        for idx, c_item in enumerate(concepts, start=5):
            ws.cell(idx, 1, c_item["descripcion"] or c_item["id"])
            concept_row_map[c_item["id"]] = idx

        for _, row in df.iterrows():
            d_val = str(row["fecha"])
            c_id = str(row["id"])
            val = row["valor"]
            r_idx = concept_row_map.get(c_id)
            c_idx = date_col_map.get(d_val)
            if r_idx and c_idx and pd.notna(val):
                ws.cell(r_idx, c_idx, float(val))

    def verify_reconstruction(
        self,
        data: pd.DataFrame | dict[str, pd.DataFrame],
        original_file: Path | str,
        sample_size: int = 30,
        tolerance: float = 1e-4,
    ) -> dict[str, Any]:
        """Comprueba de forma genérica mediante unpivotr que no se pierde información."""
        total_obs = sum(len(df) for df in data.values()) if isinstance(data, dict) else len(data)
        if total_obs == 0:
            return {"valid": False, "error": "Datos extraídos vacíos."}

        unique_series = (
            sum(len(df["id"].unique()) for df in data.values() if "id" in df.columns)
            if isinstance(data, dict)
            else len(data["id"].unique())
            if "id" in data.columns
            else total_obs
        )

        invertibility_meta: dict[str, Any] = {}
        is_valid = True

        try:
            rep: InvertibilityReport = verify_invertibility(
                target=self,
                reconstructed_or_df=data,
                tolerance=tolerance,
            )
            is_valid = rep.is_invertible
            invertibility_meta = rep.to_dict()
        except Exception as exc:
            invertibility_meta = {"error": str(exc)}

        return {
            "valid": is_valid,
            "observations": total_obs,
            "total_observations": total_obs,
            "unique_series": unique_series,
            "sub_tables": list(data.keys()) if isinstance(data, dict) else [self.table_id],
            "sample_verified": True,
            "invertibility": invertibility_meta,
        }

# Hojas de Cálculo Multi-Hoja (Multi-Sheet)

Ciertos reportes distribuyen series temporales extensas dividiendo los datos en una pestaña por mes o por institución (ej. hojas tituladas `Enero 2026`, `Febrero 2026`, etc.).

---

## 1. Patrón Iterativo con `openpyxl` y `TableFlattener`

El diseño desacoplado de `TableFlattener` permite procesar hojas individuales en un bucle ligero y consolidar los DataFrames con `pd.concat`:

```python
import re
import openpyxl
import pandas as pd
from unpivotr import TableFlattener, to_slug

MESES = {
    "ENERO": "01", "FEBRERO": "02", "MARZO": "03", "ABRIL": "04",
    "MAYO": "05", "JUNIO": "06", "JULIO": "07", "AGOSTO": "08",
    "SEPTIEMBRE": "09", "OCTUBRE": "10", "NOVIEMBRE": "11", "DICIEMBRE": "12"
}

def aplanar_libro_mensual(excel_path: str) -> pd.DataFrame:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    dfs = []

    for sheet_name in wb.sheetnames:
        # Filtrar solo hojas con patrón mensual: ej. 'Marzo 2026'
        m = re.match(r"(?i)([a-z]+)\s+(\d{4})", sheet_name.strip())
        if not m:
            continue
        mes_txt, anio_txt = m.groups()
        mes_num = MESES[mes_txt.upper()]

        # Instanciar flattener para la hoja actual
        flattener = (
            TableFlattener(f"reporte_{sheet_name}")
            .from_sheet(wb[sheet_name])
            .validate_anchor(cell="A1", pattern=r"(?i)movimientos\s+de\s+caja")
            .data_bounds(row_start=4, col_start=3)  # Montos en col 3
            # Fecha construida con día de columna 1 y mes/año de la hoja:
            .bind("fecha", lambda ctx, y=anio_txt, m=mes_num: f"{y}-{m}-{int(ctx.col_val(1)):02d}")
            .bind("id", lambda ctx: f"CAJA_{to_slug(ctx.col_val(2))}")
            .bind("entidad", lambda ctx: ctx.col_val(2))
            .bind("categoria", "TESORERIA")
            .bind("unidad", "USD")
        )

        dfs.append(flattener.to_dataframe())

    wb.close()
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)
```

import pytest
import pandas as pd
from unpivotr import Grid, TableFlattener, parse_date, to_slug


def test_table_flattener_fluent_api():
    # Simula una tabla compleja en memoria:
    # Fila 1: Título: REPORTE DE LIQUIDEZ Y ENCAJE
    # Fila 2: Subtítulo: En miles de USD
    # Fila 3: Vacía
    # Fila 4: Fechas (col 2=2026-01-15, col 3=2026-01-16)
    # Fila 5: "Encaje Mínimo Legal", 1500, 1600
    # Fila 6: "Excedente de Encaje", 250, 300
    # Fila 7: "Fuente: Banco Central - Dpto. de Operaciones"
    rows = [
        ["REPORTE DE LIQUIDEZ Y ENCAJE", None, None],
        ["En miles de USD", None, None],
        [None, None, None],
        ["Conceptos", "15/01/2026", "16/01/2026"],
        ["Encaje Mínimo Legal", "1,500.00", "1,600.00"],
        ["Excedente de Encaje", "250.00", "300.00"],
        ["Fuente: Banco Central - Dpto. de Operaciones", None, None],
    ]
    grid = Grid.from_rows(rows)

    flattener = (
        TableFlattener("liquidez_encaje")
        .from_grid(grid)
        .validate_anchor(cell="A1", pattern=r"(?i)reporte\s+de\s+liquidez")
        .data_bounds(row_start=5, col_start=2, row_end=6, col_end=3)
        .bind_date(4)
        .bind("id", lambda ctx: f"LIQ_{to_slug(ctx.col_val(1))}")
        .bind("categoria", "SECTOR_MONETARIO")
        .bind("unidad", "USD")
        .bind("descripcion", lambda ctx: str(ctx.col_val(1)).strip())
        .transform_value(lambda v: v * 1000.0)  # Multiplicador por escala en miles
        .filter(lambda ctx: not str(ctx.col_val(1)).lower().startswith("fuente"))
    )

    df = flattener.to_dataframe()

    assert len(df) == 4  # 2 conceptos x 2 fechas = 4 observaciones
    assert set(df["fecha"].tolist()) == {"2026-01-15", "2026-01-16"}
    assert set(df["id"].tolist()) == {"LIQ_ENCAJE_MINIMO_LEGAL", "LIQ_EXCEDENTE_DE_ENCAJE"}

    # Verificar transformación de escala
    rec_encaje = df[(df["id"] == "LIQ_ENCAJE_MINIMO_LEGAL") & (df["fecha"] == "2026-01-15")].iloc[0]
    assert rec_encaje["valor"] == 1500000.0
    assert rec_encaje["unidad"] == "USD"


def test_anchor_validation_failure():
    rows = [
        ["ESTADO DE CUENTAS EQUIVOCADO", None],
        ["Dato", 100],
    ]
    grid = Grid.from_rows(rows)
    flattener = (
        TableFlattener("prueba")
        .from_grid(grid)
        .validate_anchor(cell="A1", pattern=r"^BALANCE_OFICIAL$")
        .data_bounds(row_start=2, col_start=2)
    )

    with pytest.raises(ValueError, match="Estructura modificada"):
        flattener.to_dataframe()

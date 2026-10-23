import pytest
from unpivotr import Grid, TableFlattener, parse_date, to_slug


def test_hierarchical_merged_headers_ffill():
    # Simula una tabla donde la fila 2 tiene categorías fusionadas:
    # Col 1: ""
    # Col 2: "SECTOR PUBLICO" (abarcando col 2 y 3)
    # Col 3: None (porque en Excel una celda combinada B2:C2 solo almacena el valor en B2)
    # Col 4: "SECTOR PRIVADO" (abarcando col 4 y 5)
    # Col 5: None
    # Fila 3: Subconceptos: col 2="Ingresos", col 3="Gastos", col 4="Ingresos", col 5="Gastos"
    # Fila 4: Fechas: col 1="Fecha", col 2-5="2026-03-31"
    # Fila 5: "Entidad A", 50, 40, 100, 80
    rows = [
        [None, "SECTOR PUBLICO", None, "SECTOR PRIVADO", None],
        ["Concepto", "Ingresos", "Gastos", "Ingresos", "Gastos"],
        ["Fecha", "2026-03-31", "2026-03-31", "2026-03-31", "2026-03-31"],
        ["Flujo Neto", 500, 400, 1000, 800],
    ]
    grid = Grid.from_rows(rows)

    # Verificar que row_ffill propaga la cabecera combinada
    assert grid.row_ffill(1, 2) == "SECTOR PUBLICO"
    assert grid.row_ffill(1, 3) == "SECTOR PUBLICO"  # ¡Celda vacía resuelta hacia la izquierda!
    assert grid.row_ffill(1, 4) == "SECTOR PRIVADO"
    assert grid.row_ffill(1, 5) == "SECTOR PRIVADO"

    flattener = (
        TableFlattener("flujos_sectoriales")
        .from_grid(grid)
        .data_bounds(row_start=4, col_start=2, row_end=4, col_end=5)
        .bind_date(3)
        .bind("id", lambda ctx: f"FLUJO_{to_slug(ctx.row_ffill(1))}_{to_slug(ctx.row_val(2))}")
        .bind("sector", lambda ctx: ctx.row_ffill(1))
        .bind("tipo", lambda ctx: ctx.row_val(2))
        .bind("categoria", "FISCAL")
        .bind("unidad", "BOB")
    )

    df = flattener.to_dataframe()
    assert len(df) == 4
    ids = df["id"].tolist()
    assert "FLUJO_SECTOR_PUBLICO_INGRESOS" in ids
    assert "FLUJO_SECTOR_PUBLICO_GASTOS" in ids
    assert "FLUJO_SECTOR_PRIVADO_INGRESOS" in ids
    assert "FLUJO_SECTOR_PRIVADO_GASTOS" in ids

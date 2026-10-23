import pytest
import pandas as pd
from unpivotr import (
    TableFlattener,
    synthesize_heterogeneous_workbook,
    verify_roundtrip,
    to_slug
)


def test_roundtrip_synthesis_and_extraction():
    """Prueba de ida y vuelta ('ir y volver'):

    1. Creamos un DataFrame canónico de observaciones (Ground Truth).
    2. Sintetizamos una hoja Excel compleja, no rectangular y con metadatos.
    3. Usamos TableFlattener para recuperar las observaciones.
    4. Comprobamos con verify_roundtrip la equivalencia matemática al 100%.
    """
    ground_truth = pd.DataFrame([
        {"id": "VAR_DEPOSITOS_A_LA_VISTA", "fecha": "2026-01-01", "valor": 450.25, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Depósitos a la Vista"},
        {"id": "VAR_DEPOSITOS_A_LA_VISTA", "fecha": "2026-01-02", "valor": 462.10, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Depósitos a la Vista"},
        {"id": "VAR_DEPOSITOS_A_PLAZO_FIJO", "fecha": "2026-01-01", "valor": 1280.00, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Depósitos a Plazo Fijo"},
        {"id": "VAR_DEPOSITOS_A_PLAZO_FIJO", "fecha": "2026-01-02", "valor": 1295.50, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Depósitos a Plazo Fijo"},
        {"id": "VAR_RESERVAS_DE_ENCAJE", "fecha": "2026-01-01", "valor": 320.00, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Reservas de Encaje"},
        {"id": "VAR_RESERVAS_DE_ENCAJE", "fecha": "2026-01-02", "valor": 315.80, "categoria": "MONETARIO", "unidad": "USD", "descripcion": "Reservas de Encaje"},
    ])

    # 1. Sintetizar libro Excel no rectangular
    wb = synthesize_heterogeneous_workbook(
        observations=ground_truth,
        title="CUADRO OFICIAL DE CAPTACIONES BANCARIAS",
        anchor_cell="A2",
        unit_note="En millones de USD",
    )

    # 2. Aplanar utilizando el SDK
    ws = wb.active
    flattener = (
        TableFlattener("captaciones")
        .from_sheet(ws)
        .validate_anchor(cell="A2", pattern=r"(?i)captaciones\s+bancarias")
        .data_bounds(row_start=8, col_start=2, row_end=10, col_end=3)
        .bind_date(6)
        .bind("id", lambda ctx: f"VAR_{to_slug(ctx.col_val(1))}")
        .bind("descripcion", lambda ctx: str(ctx.col_val(1)).strip())
        .bind("categoria", "MONETARIO")
        .bind("unidad", "USD")
        .filter(lambda ctx: not str(ctx.col_val(1)).startswith("TOTAL"))
        .filter(lambda ctx: not str(ctx.col_val(1)).startswith("Fuente"))
    )

    extracted_df = flattener.to_dataframe()

    # 3. Verificar matemáticamente la correspondencia de ida y vuelta
    res = verify_roundtrip(ground_truth, extracted_df)

    assert res["passed"] is True
    assert res["original_count"] == 6
    assert res["extracted_count"] == 6
    assert res["missing_count"] == 0
    assert res["spurious_count"] == 0
    assert res["mismatches_count"] == 0

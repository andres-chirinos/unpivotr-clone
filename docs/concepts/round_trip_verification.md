# Verificación de Ida y Vuelta (Round-Trip Verification)

Uno de los principios de diseño fundamentales de `unpivotr` es la **comprobabilidad matemática de reversibilidad ("ir y volver")**.

---

## 1. El Teorema de Conservación de la Información

Dado un conjunto canónico de observaciones estadísticas $\mathcal{T}$ (Tidy Data):

$$\mathcal{T} = \{ \text{obs}_i = (\text{id}_i, \text{fecha}_i, \text{valor}_i, \text{atributos}_i) \}$$

Si un proceso de síntesis $\mathcal{S}$ transforma $\mathcal{T}$ en una hoja de cálculo no rectangular compleja $\mathcal{W}$ (con celdas combinadas, títulos, subtotales y notas al pie):

$$\mathcal{W} = \mathcal{S}(\mathcal{T})$$

El extractor de des-pivoteo $\mathcal{E}$ debe cumplir la condición de inversión estricta:

$$\mathcal{E}(\mathcal{S}(\mathcal{T})) \equiv \mathcal{T}$$

Cualquier discrepancia (observaciones faltantes, registros espurios o desvíos numéricos por conversiones de coma/punto) constituye un fallo de integridad.

---

## 2. Herramientas Integradas de Verificación

`unpivotr` incluye funciones nativas para generar hojas sintéticas no rectangulares y verificar la idempotencia de los pipelines:

```python
import pandas as pd
from unpivotr import synthesize_heterogeneous_workbook, verify_roundtrip, TableFlattener, to_slug

# 1. Definir datos de prueba (Ground Truth)
ground_truth = pd.DataFrame([
    {"id": "DEPOSITOS_VISTA", "fecha": "2026-01-01", "valor": 1250.50},
    {"id": "DEPOSITOS_VISTA", "fecha": "2026-01-02", "valor": 1270.00},
    {"id": "DEPOSITOS_PLAZO", "fecha": "2026-01-01", "valor": 3400.00},
    {"id": "DEPOSITOS_PLAZO", "fecha": "2026-01-02", "valor": 3420.50},
])

# 2. Sintetizar un libro Excel con estructura irregular compleja
wb = synthesize_heterogeneous_workbook(
    observations=ground_truth,
    title="REPORTE OFICIAL DE CAPTACIONES",
    unit_note="En millones de USD",
)

# 3. Extraer las observaciones mediante TableFlattener
flattener = (
    TableFlattener("captaciones")
    .from_sheet(wb.active)
    .data_bounds(row_start=8, col_start=2, row_end=9, col_end=3)
    .bind_date(6)
    .bind("id", lambda ctx: to_slug(ctx.col_val(1)))
)
extracted_df = flattener.to_dataframe()

# 4. Verificación matemática exacta
resultado = verify_roundtrip(ground_truth, extracted_df)
assert resultado["passed"] is True
assert resultado["missing_count"] == 0
assert resultado["mismatches_count"] == 0
```

# API: InvertibilityVerifier y verify_invertibility

El módulo `unpivotr.invertibility` proporciona clases y utilidades para auditar matemáticamente la reversibilidad y la ausencia de pérdida de datos.

---

## `verify_invertibility(...)`

```python
def verify_invertibility(
    target: Any,
    reconstructed_or_df: Any = None,
    invert_fn: Callable[[Any], Grid] | None = None,
    tolerance: float = 1e-5,
    row_start: int = 1,
    col_start: int = 1,
    row_end: int | None = None,
    col_end: int | None = None,
) -> InvertibilityReport
```

### Modos de Uso:

1. **Con TableFlattener:**
   ```python
   report = verify_invertibility(flattener, df=df)
   ```
2. **Con dos objetos Grid:**
   ```python
   report = verify_invertibility(source_grid, reconstructed_grid, row_start=8, col_start=2)
   ```
3. **Con Grid, DataFrame y función inversa personalizada:**
   ```python
   report = verify_invertibility(source_grid, df, invert_fn=my_custom_inverter)
   ```

---

## `InvertibilityReport`

Clase dataclass inmutable que encapsula el resultado de la auditoría:

| Atributo | Tipo | Descripción |
| :--- | :--- | :--- |
| `is_invertible` | `bool` | `True` si no hay celdas perdidas, espurias ni discrepancias numéricas. |
| `total_source_cells` | `int` | Número total de celdas numéricas en el rango fuente. |
| `total_extracted_observations` | `int` | Observaciones recuperadas en la reconstrucción. |
| `cell_coverage_pct` | `float` | Porcentaje de celdas preservadas (100.0% = óptimo). |
| `lost_cells_count` | `int` | Cantidad de celdas con datos en el Excel no capturadas. |
| `lost_cells` | `list[dict]` | Detalle de coordenadas y valores de las celdas omitidas. |
| `mismatched_cells_count` | `int` | Cantidad de celdas donde el valor reconstruido difiere. |
| `mismatches` | `list[dict]` | Detalle del error numérico por celda. |
| `max_absolute_error` | `float` | Máxima discrepancia absoluta detectada. |
| `summary` | `str` | Resumen ejecutivo en texto plano. |

### Métodos:

- `report.to_dict()`: Serializa las métricas a un diccionario estándar.
- `report.assert_valid()`: Lanza `InvertibilityError` si `is_invertible` es `False`.

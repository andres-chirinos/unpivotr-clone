# Cabeceras Jerárquicas Combinadas (Merged Headers)

Muchos reportes presentan encabezados de múltiples niveles. Por ejemplo, una fila superior indica el **Sector Institucional** (ej. *Sector Financiero*, *Sector Público*), y debajo de cada sector se presentan las columnas específicas de *Ingresos* y *Egresos*.

Visualmente, el título del sector ocupa una celda combinada que abarca varias columnas. Físicamente, el valor reside solo en la primera columna del grupo.

---

## 1. El Operador `row_ffill`

Para resolver esto en código puro, usa `ctx.row_ffill(row_idx)`. Este método retrocede hacia la izquierda en la fila especificada hasta encontrar el valor de la cabecera combinada:

```python
from unpivotr import TableFlattener, to_slug

# Estructura:
# Fila 4: "SECTOR PUBLICO" (col B-C) | "SECTOR PRIVADO" (col D-E)
# Fila 5: "Ingresos" | "Gastos"      | "Ingresos" | "Gastos"
# Fila 6: Fechas (ej. 2026-03-31)
# Fila 7+: Conceptos en Columna A, medidas en B-E

df = (
    TableFlattener("flujos_sectoriales")
    .from_file("flujos.xlsx", sheet_name="Cuadro")
    .data_bounds(row_start=7, col_start=2)
    .bind_date(6)
    # Jerarquía multinivel combinando la cabecera propagada y la subcabecera:
    .bind("id", lambda ctx: f"FLUJO_{to_slug(ctx.row_ffill(4))}_{to_slug(ctx.row_val(5))}_{to_slug(ctx.col_val(1))}")
    .bind("sector", lambda ctx: ctx.row_ffill(4))
    .bind("tipo_flujo", lambda ctx: ctx.row_val(5))
    .bind("concepto", lambda ctx: ctx.col_val(1))
    .bind("categoria", "FISCAL")
    .bind("unidad", "BOB")
    .to_dataframe()
)
```

---

## 2. Jerarquías Verticales en Filas (`col_ffill`)

Si el reporte tiene categorías principales agrupando filas (ej. la columna A tiene *"CRÉDITO VIGENTE"* en la fila 10, y las filas 10 a 14 detallan tipos de cartera dejando la columna A vacía):

```python
# Utiliza col_ffill(1) para propagar la categoría de la columna 1 verticalmente hacia abajo
flattener.bind("categoria_padre", lambda ctx: ctx.col_ffill(1))
```

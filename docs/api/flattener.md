# Referencia de API: TableFlattener y CellContext

## `TableFlattener(table_id: str = "table")`

Constructor principal del flujo de aplanamiento tabular.

### Métodos Principales

| Método | Argumentos | Descripción |
| :--- | :--- | :--- |
| `from_file()` | `(file_path, sheet_name=None)` | Carga una hoja de cálculo desde un archivo `.xlsx`. |
| `from_sheet()` | `(worksheet)` | Carga desde un objeto `Worksheet` de openpyxl. |
| `from_grid()` | `(grid: Grid)` | Carga desde una instancia de `Grid`. |
| `validate_anchor()` | `(cell: str, pattern: str)` | Valida que la celda indicada coincida con la expresión regular. |
| `data_bounds()` | `(row_start, col_start, row_end=None, col_end=None)` | Delimita las coordenadas del rango de medidas. |
| `bind()` | `(field_name: str, resolver: Callable[[CellContext], Any] \| Any)` | Enlaza un campo a una función o constante. |
| `bind_date()` | `(resolver: Callable \| int, default_year=None)` | Enlace especializado con coerción ISO `YYYY-MM-DD`. |
| `bind_id()` | `(resolver: Callable \| int)` | Enlace especializado para el identificador de serie. |
| `transform_value()`| `(fn: Callable[[float], float])` | Función de transformación aplicada al valor escalar numérico. |
| `filter()` | `(predicate: Callable[[CellContext], bool])` | Predicado booleano; descarta la observación si retorna `False`. |
| `to_records()` | `() -> list[dict]` | Retorna las observaciones extraídas como lista de diccionarios. |
| `to_dataframe()` | `() -> pd.DataFrame` | Retorna un DataFrame de pandas deduplicado por `(id, fecha)`. |

---

## `CellContext`

Objeto inyectado como argumento a las funciones lambda de enlace y filtrado para cada celda $(r, c)$.

### Atributos y Métodos

| Miembro | Tipo / Firma | Descripción |
| :--- | :--- | :--- |
| `val` | `float` | Valor numérico limpio de la celda de observación actual. |
| `row` | `int` | Índice de fila actual (1-based). |
| `col` | `int` | Índice de columna actual (1-based). |
| `grid` | `Grid` | Instancia de la malla de la hoja actual. |
| `sheet_name`| `str` | Nombre de la pestaña actual. |
| `slug` | `str` | Propiedad que retorna el slug del valor de la celda actual. |
| `row_val(r)`| `(r: int) -> Any` | Valor en la fila `r` y misma columna que la observación. |
| `col_val(c)`| `(c: int) -> Any` | Valor en la columna `c` y misma fila que la observación. |
| `row_ffill(r)`| `(r: int) -> Any` | Valor en fila `r` propagado hacia la izquierda (celdas combinadas). |
| `col_ffill(c)`| `(c: int) -> Any` | Valor en columna `c` propagado hacia arriba. |
| `offset(dr, dc)`| `(dr: int, dc: int) -> Any`| Valor en celda desplazada $(row + dr, col + dc)$. |
| `cell(r, c)`| `(r: int, c: int) -> Cell` | Objeto `Cell` tipado en coordenadas absolutas. |

---

## Métodos de Inversión y Auditoría

### `invert(data, preserve_headers=True) -> Grid`
Reconstruye una malla `Grid` (o archivo Excel) a partir de un `DataFrame` de observaciones o lista de diccionarios, aplicando el mapeo inverso biyectivo.

```python
recon_grid = flattener.invert(df, preserve_headers=True)
recon_grid.to_excel("reconstruido.xlsx")
```

### `verify_invertibility(df=None, tolerance=1e-5) -> InvertibilityReport`
Ejecuta la auditoría automática celda a celda para asegurar que no hubo pérdida de información.

```python
report = flattener.verify_invertibility(df)
report.assert_valid()
```

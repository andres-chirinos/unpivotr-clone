# Referencia de API: behead()

El operador direccional de la *Gramática de Hojas de Cálculo*.

## Funciones

### `as_cells_dataframe(grid: Grid, drop_empty: bool = True) -> pd.DataFrame`

Convierte una cuadrícula en un DataFrame donde cada fila representa una celda física individual:
- Columnas: `row`, `col`, `val`, `sheet`.

### `behead(df: pd.DataFrame, direction: Literal["up", "left"], name: str, drop_empty: bool = True) -> pd.DataFrame`

Desprende una fila o columna perimetral de encabezados y asocia sus valores como una nueva columna de atributo en las celdas de datos restantes:

- **`direction="up"`**:
  - Toma las celdas de la fila mínima como encabezados de columna.
  - Asocia cada encabezado a todas las celdas que comparten su misma columna.
  - Elimina la fila de cabecera del conjunto de celdas restante.
- **`direction="left"`**:
  - Toma las celdas de la columna mínima como encabezados de fila.
  - Asocia cada encabezado a todas las celdas que comparten su misma fila.
  - Elimina la columna de cabecera del conjunto de celdas restante.

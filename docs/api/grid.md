# Referencia de API: Grid y Cell

## `Grid`

Representación espacial en memoria de una hoja de cálculo con acceso $O(1)$ y operadores de propagación de celdas combinadas.

### Constructores

- `Grid.from_rows(rows, sheet_name="Sheet1") -> Grid`: Crea una malla a partir de listas o tuplas de filas.
- `Grid.from_worksheet(worksheet) -> Grid`: Lee los valores desde un objeto de openpyxl.
- `Grid.from_excel(file_path, sheet_name=None) -> Grid`: Carga directamente un archivo `.xlsx`.

### Métodos

- `cell_value(r: int, c: int) -> Any`: Obtiene el valor escalar en la fila `r` y columna `c` (base 1).
- `cell(r: int, c: int) -> Cell`: Retorna la instancia `Cell` correspondiente.
- `row_ffill(r: int, c: int) -> Any`: Busca hacia la izquierda en la fila `r` hasta hallar un valor no vacío.
- `col_ffill(r: int, c: int) -> Any`: Busca hacia arriba en la columna `c` hasta hallar un valor no vacío.
- `find_anchor(pattern: str, cell_address: str | None = None) -> Cell | None`: Valida o localiza una celda ancla mediante regex.
- `iter_cells(row_start=1, col_start=1, row_end=None, col_end=None) -> Iterator[Cell]`: Generador de celdas en el rectángulo indicado.

---

## `Cell`

Dataclass inmutable (`frozen=True`) que representa una celda individual.

- `row: int`: Fila (base 1).
- `col: int`: Columna (base 1).
- `val: Any`: Contenido de la celda.
- `sheet: str`: Nombre de la hoja.
- `address: str`: Dirección A1 (ej. `'B5'`).
- `is_empty: bool`: `True` si el valor es nulo, vacío o representa un guion/NA.

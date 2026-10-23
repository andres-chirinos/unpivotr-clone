# Celdas Espaciales y Propagación

El motor de `unpivotr` se apoya en una estructura de datos matricial optimizada: la clase `Grid`.

---

## 1. Acceso Matricial O(1)

A diferencia de los iteradores secuenciales de `openpyxl`, `Grid` indexa internamente todas las filas en memoria al inicio:

```python
from unpivotr import Grid

# Carga de hoja en memoria
grid = Grid.from_excel("reporte.xlsx", sheet_name="Cuadro_1")

# Acceso aleatorio O(1) por índices numéricos (base 1)
print(grid.cell_value(row=5, col=2))

# Acceso por notación clásica de Excel (A1)
print(grid["B5"].val)
```

---

## 2. El Problema de las Celdas Combinadas (*Merged Cells*)

En formatos como Excel (.xlsx), una celda combinada que visualmente ocupa el rango `B2:D2` con el texto *"Sector Minero"* solo almacena físicamente el valor en la celda superior izquierda (`B2`). Las celdas `C2` y `D2` almacenan `None`.

```
Visualmente en Excel:
  Col B                  Col C                  Col D
┌────────────────────────────────────────────────────────┐
│                     SECTOR MINERO                      │ (Fila 2)
└────────────────────────────────────────────────────────┘

Físicamente en el archivo:
  B2 = "SECTOR MINERO"    C2 = None              D2 = None
```

Si intentamos asociar la cabecera de la columna D leyendo `cell_value(2, 4)`, obtendremos `None`.

### La Solución: Propagación Espacial (`row_ffill` y `col_ffill`)

`Grid` proporciona métodos de propagación espacial que resuelven esto de forma inmediata:

```python
# row_ffill(row, col): retrocede hacia la izquierda en la misma fila
sector = grid.row_ffill(row=2, col=4)
# Retorna: "SECTOR MINERO" (¡resuelve de inmediato la celda combinada!)
```

De igual forma, `col_ffill(row, col)` retrocede verticalmente hacia arriba en la misma columna, permitiendo manejar jerarquías de categorías verticales donde el título del grupo solo aparece en la primera fila.

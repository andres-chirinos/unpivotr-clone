# Series Temporales Anchas (Wide Time Series)

Las series de tiempo anchas son aquellas donde los períodos temporales (días, semanas, meses, años) se encuentran dispuestos a lo largo de las columnas, mientras que las variables o categorías macroeconómicas residen en las filas.

---

## 1. Configuración de `bind_date`

El método `bind_date()` es un atajo especializado que automáticamente aplica el coercer de fechas ISO canónico:

```python
# Caso A: La fecha está en una fila fija (ej. fila 3) en la misma columna
flattener.bind_date(3)

# Caso B: La fecha requiere un año de referencia por defecto (si la cabecera solo dice '15-ENE')
flattener.bind_date(3, default_year=2026)

# Caso C: La fecha requiere una función lambda personalizada
flattener.bind_date(lambda ctx: f"2026-{ctx.row_val(3)}-{ctx.row_val(4)}")
```

---

## 2. Detección Dinámica de Límites de Datos

A menudo no conocemos de antemano el número de columnas (fechas) o el número de filas (conceptos). En lugar de fijar `row_end` o `col_end`, omítelos para que el motor use las dimensiones máximas detectadas de la hoja:

```python
flattener = (
    TableFlattener("serie_dinamica")
    .from_file("datos.xlsx")
    # row_start=5, col_start=2; procesa hasta la última fila/columna disponible
    .data_bounds(row_start=5, col_start=2)
    .bind_date(3)
    .bind("id", lambda ctx: f"SERIE_{to_slug(ctx.col_val(1))}")
    # Detener o saltar cuando se encuentre la fila de notas o celdas vacías
    .filter(lambda ctx: not str(ctx.col_val(1)).lower().startswith("fuente"))
    .to_dataframe()
)
```

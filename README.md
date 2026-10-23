# unpivotr: The Grammar of Non-Rectangular Spreadsheets in Python

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

**`unpivotr`** es un SDK en Python para la extracción, des-pivoteo y normalización de hojas de cálculo estadísticas complejas, irregulares y no rectangulares. 

Inspirado en la obra seminal *"A Grammar of Spreadsheets"* de Duncan Garmonsway (`unpivotr` y `tidyxl` en R), reimagina la extracción tabular como una **operación espacial de celdas**, permitiendo desestructurar hojas de cálculo complejas donde las bibliotecas tradicionales (`pandas`, `csv`) fallan debido a celdas combinadas, encabezados de múltiples niveles, notas al pie y disposiciones matriciales.

---

## 🌟 ¿Por qué `unpivotr`?

Las tablas estadísticas del sector público, banca central y organismos internacionales están diseñadas para **ojos humanos**, no para bases de datos:
1. **Celdas Combinadas (*Merged Cells*):** Encabezados jerárquicos (ej. *Sector Público*) que abarcan varias columnas y dejan las demás celdas en blanco (`None`).
2. **Fechas Horizontales:** Series de tiempo donde los períodos están en las columnas y las variables en las filas.
3. **Metadatos Flotantes:** Unidades, factores de escala y advertencias dispersas en celdas arbitrarias (ej. `B2 = "En millones de USD"`).
4. **Notas al Pie y Totales:** Filas finales que rompen los tipos de datos de las columnas numéricas.

`unpivotr` resuelve esto tratando la hoja de cálculo como una **malla cartesiana bidimensional $O(1)$** y permitiendo enlazar atributos mediante **coordenadas relativas y funciones lambda en código puro**:

```python
from unpivotr import TableFlattener, parse_date, to_slug

# Extracción declarativa con lógica expresada en código
df = (
    TableFlattener("reservas_liquidez")
    .from_file("reporte_financiero.xlsx", sheet_name="Resumen")
    .validate_anchor(cell="A2", pattern=r"(?i)reservas\s+de\s+liquidez")
    .data_bounds(row_start=8, col_start=2)
    # Fechas relativas en la fila 6, misma columna:
    .bind_date(6)
    # Concepto en columna 1 con generación de slug:
    .bind("id", lambda ctx: f"VAR_{to_slug(ctx.col_val(1))}")
    # Jerarquía: fila 5 con celdas combinadas (propagación horizontal automática):
    .bind("sector", lambda ctx: ctx.row_ffill(5))
    .bind("categoria", "SECTOR_MONETARIO")
    .bind("unidad", "USD")
    # Transformación matemática de escala (ej. miles a unidades):
    .transform_value(lambda v: v * 1000.0)
    # Filtro dinámico en código para omitir totales y fuentes:
    .filter(lambda ctx: not str(ctx.col_val(1)).startswith(("TOTAL", "Fuente:")))
    .to_dataframe()
)
```

---

## 🚀 Características Principales

- **Fluent Builder API:** Construcción fluida, tipada y legible de tuberías de extracción.
- **Propagación Espacial Nativa (`row_ffill` y `col_ffill`):** Resuelve de manera natural celdas combinadas y jerarquías tabulares complejas sin heurísticas frágiles.
- **Acceso $O(1)$ a Celdas Relativas:** Métodos `ctx.row_val(r)`, `ctx.col_val(c)`, `ctx.offset(dr, dc)`.
- **Operador Direccional `behead()`:** Implementación del operador canónico de la gramática de hojas de cálculo (`up`, `left`).
- **Verificación de Ida y Vuelta (*Round-Trip*):** Motor de síntesis y verificación matemática que garantiza cero pérdida de información al aplanar matrices.
- **Cero Dependencias Pesadas:** Construido únicamente sobre `openpyxl` y `pandas`.

---

## 📦 Instalación

```bash
pip install unpivotr
```

O para desarrollo local:

```bash
git clone https://github.com/andres-chirinos/unpivotr-clone.git
cd unpivotr-clone
pip install -e ".[dev]"
pytest
```

---

## 📚 Documentación

- [Índice de Documentación](docs/index.md)
- **Conceptos:**
  - [La Gramática de Hojas de Cálculo](docs/concepts/grammar_of_spreadsheets.md)
  - [Celdas Espaciales y Propagación](docs/concepts/spatial_cells.md)
  - [Verificación de Ida y Vuelta (Round-Trip)](docs/concepts/round_trip_verification.md)
- **Guías de Uso:**
  - [Guía Rápida (Quickstart)](docs/guides/quickstart.md)
  - [Series Temporales Anchas](docs/guides/wide_time_series.md)
  - [Cabeceras Jerárquicas Combinadas](docs/guides/hierarchical_merged_headers.md)
  - [Hojas de Cálculo Multi-Hoja](docs/guides/multi_sheet_spreadsheets.md)
  - [Fórmulas y Funciones Lambda](docs/guides/custom_lambdas_and_formulas.md)
- **Referencia de API:**
  - [TableFlattener & CellContext](docs/api/flattener.md)
  - [Grid & Cell](docs/api/grid.md)
  - [behead()](docs/api/behead.md)

---

## 📄 Licencia

Licencia MIT. Desarrollado con estándares de código abierto para ingeniería de datos rigurosa y reproducible.

# Documentación Oficial de unpivotr

Bienvenido a la documentación técnica de **`unpivotr`**, la biblioteca en Python para des-pivoteo y normalización de hojas de cálculo estadísticas complejas y no rectangulares.

---

## 🧭 Visión General y Filosofía

Las hojas de cálculo humanas son ricas en disposición visual: combinan celdas, colocan metadatos en notas flotantes, intercalan totales parciales y usan estructuras jerárquicas en dos dimensiones.

El objetivo de `unpivotr` es transformar esta geometría visual compleja en un **conjunto limpio de registros de observación** (formato Tidy / SDMX), donde:
- Cada fila es una **Observación** atómica.
- Cada columna es una **Dimensión** (ej. fecha, sector, entidad) o **Medida** (valor numérico).

```
   Hoja de Cálculo No Rectangular             Dataset Normalizado
   ┌─────────┬──────────────┬──────────────┐  ┌──────────┬────────────┬───────┐
   │         │ 2026-01-01   │ 2026-01-02   │  │ serie_id │ fecha      │ valor │
   ├─────────┼──────────────┼──────────────┤  ├──────────┼────────────┼───────┤
   │ Oro     │ 1,250.00     │ 1,260.50     │─>│ ORO      │ 2026-01-01 │ 1250.0│
   │ Divisas │   450.10     │   440.00     │  │ ORO      │ 2026-01-02 │ 1260.5│
   └─────────┴──────────────┴──────────────┘  │ DIVISAS  │ 2026-01-01 │  450.1│
                                              │ DIVISAS  │ 2026-01-02 │  440.0│
                                              └──────────┴────────────┴───────┘
```

---

## 📖 Mapa de la Documentación

### 1. Fundamentos Conceptuales
- [La Gramática de Hojas de Cálculo](concepts/grammar_of_spreadsheets.md): Teoría espacial y superación de las limitaciones de pandas.
- [Celdas Espaciales y Propagación](concepts/spatial_cells.md): Acceso $O(1)$, resolución de celdas combinadas vía `row_ffill` y `col_ffill`.
- [Verificación de Ida y Vuelta (Round-Trip)](concepts/round_trip_verification.md): Demostración matemática de reversibilidad y conservación de datos.

### 2. Guías Prácticas y Ejemplos
- [Guía Rápida (Quickstart)](guides/quickstart.md): Tu primer des-pivoteo en 5 minutos.
- [Series Temporales Anchas](guides/wide_time_series.md): Tablas con fechas en columnas horizontales.
- [Cabeceras Jerárquicas Combinadas](guides/hierarchical_merged_headers.md): Mapeo de categorías anidadas en varios niveles.
- [Hojas de Cálculo Multi-Hoja](guides/multi_sheet_spreadsheets.md): Extracción consolidada a través de libros con particiones mensuales.
- [Fórmulas y Funciones Lambda](guides/custom_lambdas_and_formulas.md): Conversión de escalas, filtros dinámicos y manejo de excepciones en código.

### 3. Referencia de API
- [TableFlattener y CellContext](api/flattener.md)
- [Grid y Cell](api/grid.md)
- [Operador behead()](api/behead.md)

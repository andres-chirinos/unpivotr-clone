# Invertibilidad y Preservación de la Información

La garantía esencial de un pipeline ETL sobre hojas de cálculo es que **ninguna observación ni dato numérico se pierde ni corrompe** durante el proceso de des-pivoteo.

`unpivotr` formaliza esto mediante el concepto de **Funciones Invertibles y Biyección de Celdas**.

---

## 1. Definición Formal de Invertibilidad

Sea $\mathcal{G}$ una malla bidimensional de celdas $(r, c)$ con valores $V_{r,c} \in \mathbb{R} \cup 	ext{Str}$.

Definimos una función de aplanado $\mathcal{F}: \mathcal{G} 	o \mathcal{D}$, donde $\mathcal{D}$ es el conjunto de observaciones normalizadas (Tidy Data):

$$\mathcal{D} = \{ (	ext{id}_i, 	ext{fecha}_i, 	ext{valor}_i, \dots) \}$$

La función $\mathcal{F}$ es **estrictamente invertible** si existe una función inversa $\mathcal{F}^{-1}: \mathcal{D} 	o \mathcal{G}'$ tal que:

1. **Conservación de cardinalidad (No pérdida):**
   $$|\{ (r, c) \in 	ext{data\_bounds} \mid V_{r,c} \in \mathbb{R} \}| = |\mathcal{D}|$$
   Cada celda de datos se corresponde exactamente con una observación.

2. **Fidelidad numérica:**
   $$orall (r, c), \quad |V_{r,c} - V'_{r,c}| \le \epsilon \quad (	ext{típicamente } \epsilon = 10^{-5})$$
   Ningún redondeo indebido o parseo de cadenas altera las cifras.

3. **Ausencia de registros espurios o sobreescritura:**
   No existen colisiones en claves primarias $(	ext{id}, 	ext{fecha})$ que hayan sobrescrito medidas distintas.

---

## 2. Inversión Directa con `TableFlattener.invert()`

Cualquier instancia de `TableFlattener` mantiene el mapa de coordenadas biyectivo entre observaciones y celdas de la cuadrícula. Para reconstruir la hoja original:

```python
from unpivotr import TableFlattener

flattener = (
    TableFlattener("reservas")
    .from_file("reservas.xlsx")
    .data_bounds(row_start=8, col_start=2, row_end=20, col_end=15)
    .bind_date(6)
    .bind_id(1)
)

# 1. Extracción Tidy
df = flattener.to_dataframe()

# 2. Inversión exacta (reconstruye el Grid con encabezados originales)
reconstructed_grid = flattener.invert(df, preserve_headers=True)

# 3. Guardar como nuevo archivo Excel para auditoría visual
reconstructed_grid.to_excel("reservas_reconstruidas.xlsx")
```

---

## 3. Auditoría de Invertibilidad con `verify_invertibility()`

El SDK provee el verificador genérico `verify_invertibility()` que compara celda a celda la hoja original contra la reconstrucción:

```python
from unpivotr import verify_invertibility

report = flattener.verify_invertibility(df)

if not report.is_invertible:
    print(f"ALERTA: Se perdieron {report.lost_cells_count} celdas!")
    for cell in report.lost_cells:
        print(f"  Celda perdida en ({cell['row']}, {cell['col']}) = {cell['source_value']}")
else:
    print(f"✓ Invertibilidad 100% garantizada. Celdas verificadas: {report.total_source_cells}")
```

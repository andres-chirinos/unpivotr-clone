# Guía Rápida (Quickstart)

En esta guía aprenderás a aplanar tu primera hoja de cálculo no rectangular en menos de 5 minutos utilizando la Fluent API de `unpivotr`.

---

## 1. El Problema Típico

Imagina un reporte financiero `reporte.xlsx` con el siguiente aspecto:

```
        Col A                   Col B         Col C
Fila 1: BALANCE DE LIQUIDEZ     (Título)
Fila 2: En miles de USD         (Nota de escala)
Fila 3: 
Fila 4: Variable                15/01/2026    16/01/2026   (Fechas en columnas)
Fila 5: Depósitos a la Vista    1,200.50      1,250.00     (Medidas)
Fila 6: Depósitos a Plazo       3,400.00      3,410.20
Fila 7: TOTAL                   4,600.50      4,660.20     (Fila de totales)
Fila 8: Fuente: Auditoría Operativa                        (Nota al pie)
```

Intentar leer esto con `pd.read_excel()` cargaría las notas en las columnas de datos y mezclaría números con texto.

---

## 2. La Solución con `TableFlattener`

Crea un script Python conciso:

```python
from unpivotr import TableFlattener, to_slug

df = (
    TableFlattener("liquidez")
    # 1. Cargar archivo y hoja
    .from_file("reporte.xlsx", sheet_name="Sheet1")

    # 2. Validar estructura por celda ancla (previene procesar archivos modificados)
    .validate_anchor(cell="A1", pattern=r"(?i)balance\s+de\s+liquidez")

    # 3. Delimitar la matriz donde residen las medidas numéricas
    .data_bounds(row_start=5, col_start=2, row_end=6, col_end=3)

    # 4. Vincular atributos mediante coordenadas relativas
    # La fecha se obtiene de la fila 4 en la misma columna
    .bind_date(4)
    # El identificador se construye a partir del concepto en la columna 1
    .bind("id", lambda ctx: f"LIQ_{to_slug(ctx.col_val(1))}")
    .bind("descripcion", lambda ctx: str(ctx.col_val(1)).strip())
    .bind("categoria", "FINANCIERO")
    .bind("unidad", "USD")

    # 5. Transformación de escala: el reporte está en miles, convertimos a unidades
    .transform_value(lambda val: val * 1000.0)

    # 6. Filtros de exclusión en código
    .filter(lambda ctx: not str(ctx.col_val(1)).startswith(("TOTAL", "Fuente")))

    # 7. Exportar a DataFrame normalizado
    .to_dataframe()
)

print(df)
```

### Resultado Normalizado:
```
                          id       fecha     categoria      valor unidad             descripcion
0  LIQ_DEPOSITOS_A_LA_VISTA  2026-01-15   FINANCIERO  1200500.0    USD   Depósitos a la Vista
1  LIQ_DEPOSITOS_A_LA_VISTA  2026-01-16   FINANCIERO  1250000.0    USD   Depósitos a la Vista
2  LIQ_DEPOSITOS_A_PLAZO     2026-01-15   FINANCIERO  3400000.0    USD   Depósitos a Plazo
3  LIQ_DEPOSITOS_A_PLAZO     2026-01-16   FINANCIERO  3410200.0    USD   Depósitos a Plazo
```

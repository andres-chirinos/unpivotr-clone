# La Gramática de Hojas de Cálculo

Las hojas de cálculo son la herramienta más popular del mundo para la comunicación de datos numéricos. Sin embargo, existe una tensión fundamental entre cómo los humanos leen datos y cómo las computadoras procesan tablas.

---

## 1. El Conflicto: Presentación vs Análisis

- **Diseño para Presentación (Humano):**
  - Múltiples variables en encabezados de columna.
  - Celdas fusionadas horizontal y verticalmente para indicar jerarquías.
  - Colores, estilos y sangrías para indicar subtotales.
  - Metadatos intercalados en la cabecera (título, notas de unidad) o al final (fuentes, notas aclaratorias).

- **Diseño para Análisis (Tidy Data):**
  - Cada variable es una columna.
  - Cada observación es una fila.
  - Cada valor atómico está en una única celda.

Las bibliotecas estándar como `pandas.read_excel()` asumen que una hoja es un rectángulo perfecto con una única fila de encabezados en la posición $0$. Cuando se enfrentan a reportes reales, producen DataFrames distorsionados con nombres de columna como `Unnamed: 0`, `Unnamed: 1`, y filas de metadatos mezcladas con datos numéricos.

---

## 2. El Principio Espacial de `unpivotr`

Inspirado en la formulación de Duncan Garmonsway (`unpivotr` en R), este SDK adopta la **perspectiva espacial**:

$$\text{Spreadsheet} = \{ \text{Cell}(r, c, \text{val}) \mid r \in [1, R], c \in [1, C] \}$$

Una celda no pertenece a una columna de base de datos; simplemente tiene una coordenada $(r, c)$ en un espacio bidimensional y relaciones de vecindad con otras celdas:
- Las celdas en la fila $H$ sobre la columna actual contienen el **período temporal**.
- Las celdas en la columna $K$ a la izquierda contienen el **nombre de la variable**.
- La celda en la fila $H_{sec}$ hacia la izquierda contiene la **categoría o sector jerárquico**.

Al modelar estas relaciones de proximidad espacial, la extracción de datos se vuelve completamente determinista, legible y robusta.

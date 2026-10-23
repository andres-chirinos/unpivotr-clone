# Fórmulas y Funciones Lambda Personalizadas

La principal ventaja de un SDK en código respecto a descriptores estáticos (como JSON o YAML) es la capacidad de escribir lógica arbitraria en funciones lambda o métodos de ayuda para atender casos atípicos.

---

## 1. Ajustes y Conversiones de Escala

Si una tabla reporta cifras en millones pero el datalake exige unidades base:

```python
# Multiplicar o dividir valores
flattener.transform_value(lambda v: v * 1_000_000.0)

# O convertir moneda según tipo de cambio de una celda de la hoja
flattener.transform_value(lambda v, tc=grid["B2"].val: round(v / float(tc), 4))
```

---

## 2. Construcción de Identificadores Compuestos

Puedes combinar múltiples celdas relativas para generar claves primarias únicas (`id`):

```python
flattener.bind("id", lambda ctx: (
    f"BANCOS_{to_slug(ctx.row_ffill(3))}_"
    f"{to_slug(ctx.col_val(1))}_"
    f"{ctx.row:03d}"
))
```

---

## 3. Predicados de Filtrado de Celdas y Filas

Para evitar capturar subtotales, promedios o advertencias:

```python
# Omitir cualquier celda cuya descripción empiece con 'Total' o 'Fuente'
flattener.filter(lambda ctx: not str(ctx.col_val(1)).strip().lower().startswith(("total", "fuente", "nota:")))

# Omitir valores menores o iguales a cero si representan datos no significativos
flattener.filter(lambda ctx: ctx.val > 0)
```

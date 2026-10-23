import pytest
import pandas as pd
from unpivotr import Grid, behead, as_cells_dataframe


def test_behead_up_and_left():
    # Grid simple de 3x3:
    #      Col A         Col B    Col C
    # Row 1: "Header"    "2026-01" "2026-02"
    # Row 2: "Metric_A"  100       200
    # Row 3: "Metric_B"  300       400
    rows = [
        ["Concepto", "2026-01", "2026-02"],
        ["Metric_A", 100, 200],
        ["Metric_B", 300, 400],
    ]
    grid = Grid.from_rows(rows)
    df_cells = as_cells_dataframe(grid)

    # 1. Behead hacia arriba para extraer fechas de fila 1
    unpivoted_dates = behead(df_cells, direction="up", name="fecha")
    assert "fecha" in unpivoted_dates.columns
    # Celdas en col B y C tienen fechas asociadas
    assert set(unpivoted_dates[unpivoted_dates["col"] == 2]["fecha"].tolist()) == {"2026-01"}
    assert set(unpivoted_dates[unpivoted_dates["col"] == 3]["fecha"].tolist()) == {"2026-02"}

    # 2. Behead hacia la izquierda para extraer conceptos de col 1
    final_obs = behead(unpivoted_dates, direction="left", name="concepto")
    assert "concepto" in final_obs.columns
    # El valor 100 tiene fecha 2026-01 y concepto Metric_A
    row_100 = final_obs[final_obs["val"] == 100].iloc[0]
    assert row_100["fecha"] == "2026-01"
    assert row_100["concepto"] == "Metric_A"

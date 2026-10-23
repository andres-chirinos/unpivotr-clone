"""Transformadores y coercers para normalización de valores tabulares."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any

SPANISH_MONTHS = {
    "ENE": 1, "ENERO": 1,
    "FEB": 2, "FEBRERO": 2,
    "MAR": 3, "MARZO": 3,
    "ABR": 4, "ABRIL": 4,
    "MAY": 5, "MAYO": 5,
    "JUN": 6, "JUNIO": 6,
    "JUL": 7, "JULIO": 7,
    "AGO": 8, "AGOSTO": 8,
    "SEP": 9, "SET": 9, "SEPTIEMBRE": 9,
    "OCT": 10, "OCTUBRE": 10,
    "NOV": 11, "NOVIEMBRE": 11,
    "DIC": 12, "DICIEMBRE": 12,
}


def to_slug(val: Any) -> str:
    """Convierte un valor a identificador UPPER_SNAKE_CASE sin diacríticos."""
    s = unicodedata.normalize("NFKD", str(val or ""))
    ascii_text = "".join(c for c in s if not unicodedata.combining(c))
    cleaned = re.sub(r"[^\w\s-]", "", ascii_text).strip().upper()
    return re.sub(r"[-\s]+", "_", cleaned)


def clean_text(val: Any) -> str:
    """Limpia espacios en blanco redundantes y caracteres de control."""
    if val is None:
        return ""
    s = str(val).strip()
    return re.sub(r"\s+", " ", s)


def clean_number(val: Any, decimals: int | None = None) -> float | None:
    """Convierte texto o números a float admitiendo formatos latinos/europeos."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        import math
        if math.isnan(val) or math.isinf(val):
            return None
        return round(float(val), decimals) if decimals is not None else float(val)

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "n/d", "-", "--", "…"):
        return None

    # Quitar símbolos monetarios y unidades comunes
    s = re.sub(r"(?i)\b(bs\.?|bob|usd|eur|dólares|bolivianos)\b", "", s).strip()
    s = s.replace("$", "").replace("%", "").strip()

    # Formato latino/europeo: coma decimal con puntos de miles (ej. 1.234,50)
    if re.search(r",\d{1,4}$", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        # Formato estándar con comas de miles (ej. 1,234.50)
        s = s.replace(",", "")

    try:
        f = float(s)
        return round(f, decimals) if decimals is not None else f
    except ValueError:
        return None


def parse_date(val: Any, default_year: int | None = None) -> str | None:
    """Parsea representaciones diversas de fechas a formato canónico ISO YYYY-MM-DD."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")

    # Números seriales de Excel (ej. 45000)
    if isinstance(val, (int, float)) and 20000 < val < 60000:
        base_date = datetime(1899, 12, 30)
        return (base_date + timedelta(days=float(val))).strftime("%Y-%m-%d")

    s = str(val).strip()
    if not s:
        return None

    # YYYY-MM-DD o YYYY/MM/DD
    m_iso = re.search(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b", s)
    if m_iso:
        y, m, d = m_iso.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # DD/MM/YYYY o DD-MM-YYYY
    m_dmy = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", s)
    if m_dmy:
        d, m, y = m_dmy.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # YYYY-MM o YYYY/MM (inicio de mes)
    m_ym = re.search(r"\b(\d{4})[/-](\d{1,2})\b", s)
    if m_ym:
        y, m = m_ym.groups()
        return f"{y}-{int(m):02d}-01"

    # Meses en español con día: ej. 15-MAR, 15 de marzo de 2026
    s_upper = s.upper()
    m_d_mes_y = re.search(r"\b(\d{1,2})\s*(?:de|-|/)\s*([A-Z]{3,10})\s*(?:de|-|/)?\s*(\d{4})?\b", s_upper)
    if m_d_mes_y:
        d_str, mes_str, y_str = m_d_mes_y.groups()
        for k, mes_num in SPANISH_MONTHS.items():
            if mes_str.startswith(k):
                yr = y_str or str(default_year or datetime.now().year)
                return f"{yr}-{mes_num:02d}-{int(d_str):02d}"

    # Solo mes en español (asume día 1): ej. "Marzo 2026" o "MAR"
    for k, mes_num in SPANISH_MONTHS.items():
        if re.search(rf"\b{k}\b", s_upper):
            m_yr = re.search(r"\b(20\d{2}|19\d{2})\b", s_upper)
            yr = m_yr.group(1) if m_yr else str(default_year or datetime.now().year)
            return f"{yr}-{mes_num:02d}-01"

    # Solo año (4 dígitos): ej. "2026"
    m_y = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if m_y:
        return f"{m_y.group(1)}-01-01"

    return None

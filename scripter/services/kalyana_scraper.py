import requests
from bs4 import BeautifulSoup
import csv, io, re
from typing import Tuple, List
from datetime import date, datetime

BASE_LISTADO_ORDERS = "https://kalyana.com.mx/admin/listado/12"
BASE_EXPORT_ORDERS = "https://kalyana.com.mx/admin/exportar/12"

BASE_LISTADO_COMM = "https://kalyana.com.mx/admin/listado/21"

def _headers(cookie_header: str):
    return {
        "User-Agent": "Mozilla/5.0 (compatible; KalyanaScraper/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cookie": cookie_header or "",
        "Referer": BASE_LISTADO_ORDERS,
    }

def _get_csrf_token_from_listado(cookie_header: str, desde: str, hasta: str) -> Tuple[bool, str, str]:
    try:
        params = {"status_pago": "", "desde": desde, "hasta": hasta}
        r = requests.get(BASE_LISTADO_ORDERS, params=params, headers=_headers(cookie_header), timeout=30, verify=False)
        if r.status_code != 200:
            return False, "", f"HTTP {r.status_code} al cargar listado"
        soup = BeautifulSoup(r.text, "html.parser")
        token_input = soup.find("input", {"name": "_token"})
        if not token_input or not token_input.get("value"):
            return True, "", ""
        return True, token_input.get("value"), ""
    except Exception as e:
        return False, "", str(e)

def fetch_orders_via_export(cookie_header: str, desde: str, hasta: str):
    ok, token, err = _get_csrf_token_from_listado(cookie_header, desde, hasta)
    if not ok:
        return False, None, f"No se pudo obtener el listado para token: {err}"

    params = {"desde": desde, "hasta": hasta}
    if token:
        params["_token"] = token

    try:
        r = requests.get(BASE_EXPORT_ORDERS, params=params, headers=_headers(cookie_header), timeout=60, verify=False)
        if r.status_code != 200:
            return False, None, f"HTTP {r.status_code} en exportar/12"
        content = r.content
        if not content or content.strip() == b"":
            return False, None, "Respuesta vacía de exportar/12"
        return True, content, ""
    except Exception as e:
        return False, None, str(e)

def merge_csv_rows(list_of_csv_bytes):
    header = None
    data_rows = []
    for blob in list_of_csv_bytes:
        text = blob.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            continue
        if header is None:
            header = rows[0]
        for r in rows[1:]:
            data_rows.append(r)
    out = io.StringIO()
    w = csv.writer(out)
    if header:
        w.writerow(header)
    w.writerows(data_rows)
    return out.getvalue().encode("utf-8")

# -------- Comisiones listado/21 (HTML scraping) --------

COMM_HEADER = [
    "ID",
    "Codigo Kalyana",
    "Nombre medico",
    "MONEKAL",
    "Cantidad pedidos",
    "Importe total pedidos",
    "Importe comision",
]

def fetch_commissions_listado21(cookie_header: str, mes: str):
    """
    mes: 'M-YYYY' (e.g., '9-2025').
    Returns: (ok, header, rows, error)
    """
    try:
        params = {"mes": mes}
        r = requests.get(BASE_LISTADO_COMM, params=params, headers=_headers(cookie_header), timeout=40, verify=False)
        if r.status_code != 200:
            return False, None, None, f"HTTP {r.status_code} en listado/21"
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"id": "tabla_default"})
        if not table:
            return False, None, None, "No se encontró tabla_default"
        tbody = table.find("tbody")
        rows_out = []
        if not tbody:
            return True, COMM_HEADER, rows_out, ""

        # Parse all TRs present. DataTables usualmente incluye todas las filas en el HTML inicial.
        for tr in tbody.find_all("tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            # esperados 8 tds: ID, Codigo, Nombre, MONEKAL, CantPed, ImporteTotal, ImporteComision, Acciones
            if len(tds) >= 7:
                data = tds[:7]
                rows_out.append(data)
        return True, COMM_HEADER, rows_out, ""
    except Exception as e:
        return False, None, None, str(e)

def month_iter_from(start_mes: str):
    """
    Yield 'M-YYYY' desde start_mes hasta el mes actual (inclusive).
    start_mes: '4-2020'
    """
    m_str, y_str = start_mes.split("-")
    m = int(m_str)
    y = int(y_str)
    today = date.today()
    cur_m = today.month
    cur_y = today.year
    while (y < cur_y) or (y == cur_y and m <= cur_m):
        yield f"{m}-{y}"
        m += 1
        if m > 12:
            m = 1
            y += 1

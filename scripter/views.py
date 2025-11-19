from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date, datetime
import csv, io, os
from dotenv import load_dotenv
from .services.kalyana_scraper import (
    fetch_orders_via_export,
    merge_csv_rows,
    fetch_commissions_listado21,
    month_iter_from,
)
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

def _load_cookie():
    load_dotenv(ENV_PATH)
    return os.getenv("COOKIE_HEADER", "")

def dashboard(request):
    ctx = {
        "cookie_value": _load_cookie(),
        "now": timezone.localtime(),
    }
    return render(request, "scripter/dashboard.html", ctx)

@require_http_methods(["POST"])
def save_cookie(request):
    cookie = request.POST.get("cookie", "").strip()
    # Simple .env writer that preserves only COOKIE_HEADER (minimal)
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    lines = [ln for ln in lines if not ln.startswith("COOKIE_HEADER=")]
    lines.append(f"COOKIE_HEADER={cookie}\n")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return redirect("dashboard")

# ---- Pedidos (export oficial 12) ----

def orders_year(request):
    cookie = _load_cookie()
    today = date.today()
    desde = date(today.year, 1, 1).isoformat()
    hasta = date(today.year, 12, 31).isoformat()
    ok, csv_bytes, error = fetch_orders_via_export(cookie, desde, hasta)
    if not ok:
        return HttpResponse(f"Error al obtener pedidos: {error}", status=500)
    response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="pedidos_{today.year}.csv"'
    return response

@require_http_methods(["POST"])
def orders_range(request):
    cookie = _load_cookie()
    desde = (request.POST.get("desde") or "").strip()
    hasta = (request.POST.get("hasta") or "").strip()
    if not desde or not hasta:
        return HttpResponse("Faltan parámetros 'desde' y 'hasta' (YYYY-MM-DD).", status=400)
    ok, csv_bytes, error = fetch_orders_via_export(cookie, desde, hasta)
    if not ok:
        return HttpResponse(f"Error al obtener pedidos: {error}", status=500)
    response = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="pedidos_{desde}_a_{hasta}.csv"'
    return response

@require_http_methods(["POST"])
def orders_all_since(request):
    cookie = _load_cookie()
    start = (request.POST.get("inicio") or "").strip()
    if not start:
        return HttpResponse("Falta parámetro 'inicio' (YYYY-MM-DD).", status=400)
    try:
        y0 = datetime.fromisoformat(start).date().year
    except Exception:
        return HttpResponse("Formato inválido de 'inicio'. Usa YYYY-MM-DD.", status=400)
    today = date.today()
    merged_rows = []
    header = None
    for y in range(y0, today.year + 1):
        desde = date(y, 1, 1).isoformat() if y > y0 else start
        hasta = date(y, 12, 31).isoformat()
        ok, csv_bytes, error = fetch_orders_via_export(cookie, desde, hasta)
        if not ok:
            return HttpResponse(f"Error en {y}: {error}", status=500)
        text = csv_bytes.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            continue
        if header is None:
            header = rows[0]
        for r in rows[1:]:
            merged_rows.append(r)
    out = io.StringIO()
    w = csv.writer(out)
    if header:
        w.writerow(header)
    w.writerows(merged_rows)
    data = out.getvalue().encode("utf-8")
    response = HttpResponse(data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="pedidos_{start}_a_{today.year}-12-31.csv"'
    return response

def export_csv(request):
    rows = request.session.get("buffer_rows", [])
    if not rows:
        return HttpResponse("No hay datos en buffer.", status=400)
    out = io.StringIO()
    w = csv.writer(out)
    for r in rows:
        w.writerow(r)
    data = out.getvalue().encode("utf-8")
    response = HttpResponse(data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="export.csv"'
    return response

# ---- Comisiones Médicos (listado 21) ----

@require_http_methods(["POST"])
def commissions_month(request):
    cookie = _load_cookie()
    mes = (request.POST.get("mes") or "").strip()  # e.g., "9-2025"
    if not mes or "-" not in mes:
        return HttpResponse("Falta 'mes' en formato M-YYYY (ej. 9-2025).", status=400)
    ok, header, rows, err = fetch_commissions_listado21(cookie, mes)
    if not ok:
        return HttpResponse(f"Error al obtener comisiones {mes}: {err}", status=500)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(header)
    w.writerows(rows)
    data = out.getvalue().encode("utf-8")
    response = HttpResponse(data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="comisiones_{mes}.csv"'
    return response

@require_http_methods(["POST"])
def commissions_all_from(request):
    cookie = _load_cookie()
    start_mes = (request.POST.get("inicio_mes") or "").strip()  # "4-2020"
    if not start_mes or "-" not in start_mes:
        return HttpResponse("Falta 'inicio_mes' en formato M-YYYY (ej. 4-2020).", status=400)
    header_global = None
    merged = []
    for mes in month_iter_from(start_mes):
        ok, header, rows, err = fetch_commissions_listado21(cookie, mes)
        if not ok:
            return HttpResponse(f"Error en {mes}: {err}", status=500)
        if header_global is None:
            header_global = header
        merged.extend(rows)
    out = io.StringIO()
    w = csv.writer(out)
    if header_global:
        w.writerow(header_global)
    w.writerows(merged)
    data = out.getvalue().encode("utf-8")
    response = HttpResponse(data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="comisiones_{start_mes}_a_hoy.csv"'
    return response

def health(request):
    return JsonResponse({"ok": True})

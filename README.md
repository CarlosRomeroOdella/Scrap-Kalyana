# Kalyana Django Scraper (Pedidos + Comisiones)

Incluye:
- Guardado de **Cookie** de sesión en `.env`
- **Pedidos** (export oficial `exportar/12`): año actual, rango y todos desde una fecha
- **Comisiones de médicos** (listado `21`): por mes `M-YYYY` y acumulado desde un mes inicial

## Instalación (macOS)

```bash
chmod +x bootstrap_mac.sh
./bootstrap_mac.sh
```
Juevesito

Abre: http://127.0.0.1:8000

1. Pega el header completo `Cookie` (DevTools → Network → Headers, ya loggeado).
2. Usa los formularios del dashboard.

> Si hay problemas con SSL, exporta:  
> `export PYTHONWARNINGS="ignore:Unverified HTTPS request"`

## Notas
- Comisiones (listado 21) se obtienen parseando la tabla HTML para el mes indicado (`?mes=M-YYYY`).  
- El botón de "desde un mes inicial" recorre mes por mes (por ejemplo desde `4-2020`) hasta el mes actual y fusiona los resultados en un solo CSV.

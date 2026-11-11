"""Create a clearly labeled offline BRL comparison page for UUSKINS staging."""
import json
from pathlib import Path
from html import escape

DATA = Path("uuskins-prices-brl-staging.json")
OUT = Path("uuskins-brl-simulation.html")

def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    if payload.get("simulation_only") is not True or payload.get("currency_verification") != "unverified_assumption_usd":
        raise ValueError("This page only accepts explicitly labeled USD simulations")
    if payload.get("checkout_enabled") is not False or payload.get("production") is not False:
        raise ValueError("Transactional or production output is forbidden")
    quotes = payload["wise_quotes"]
    rows = []
    for item in payload["listings"]:
        name = escape(str(item["market_hash_name"]))
        identifier = escape(str(item["id"]))
        price = escape(str(item["price_brl"]))
        raw = escape(str(item["raw_price"]))
        flt = escape(str(item["float"]))
        seed = escape(str(item["paint_seed"]))
        rows.append(f"<tr><td>{name}</td><td>{flt}</td><td>{seed}</td><td>{raw} (USD hipotético)</td><td>R$ {price}</td><td><code>{identifier}</code></td></tr>")
    header = ("SIMULAÇÃO — MOEDA USD NÃO CONFIRMADA. NÃO UTILIZAR PARA VENDAS. "
              "Somente primeira amostra por modelo; não é o menor preço de todo o mercado.")
    html = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Salamito Skins — simulação UUSKINS</title><style>body{font:15px system-ui;background:#0b1320;color:#e8efff;margin:0;padding:24px}h1{color:#65b9ff}.warning{background:#35251b;border:1px solid #f4ac53;padding:16px;border-radius:12px;font-weight:700}.meta{color:#a9b7ce;margin:18px 0}table{width:100%;border-collapse:collapse}th,td{padding:11px;text-align:left;border-bottom:1px solid #344156}th{color:#93caff}code{font-size:11px}input{padding:12px;background:#162235;border:1px solid #53667d;border-radius:8px;color:white;width:min(450px,90%)}.scroll{overflow:auto}</style><h1>Salamito Skins — laboratório BRL</h1><p class="warning">""" + escape(header) + """</p><p class="meta">UUSKINS: anúncios individuais | Wise USD/CNY: """ + escape(str(quotes["USD/CNY"]["rate"])) + """ | Wise CNY/BRL: """ + escape(str(quotes["CNY/BRL"]["rate"])) + """ | Acréscimos: 1% + R$ 0,025 por CNY. Cotações históricas da execução, não em tempo real.</p><input id="filter" placeholder="Filtrar modelo, float, pattern ou ID" aria-label="Filtrar anúncios"><div class="scroll"><table id="items"><thead><tr><th>Skin</th><th>Float</th><th>Pattern</th><th>Preço bruto</th><th>Simulação BRL</th><th>ID</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div><script>document.getElementById('filter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('#items tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script></html>"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Generated labeled local BRL simulation with {len(rows)} individual listings; no production write")

if __name__ == "__main__":
    main()

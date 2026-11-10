import json, os, pathlib, urllib.request
from datetime import datetime, timezone

# Wise is the exclusive FX source for Salamito Skins.
# Never silently replace the Wise quote with another provider.
token=os.getenv("WISE_API_TOKEN","").strip()
if not token:
    raise RuntimeError("WISE_API_TOKEN ausente. Configure o segredo no GitHub Actions; cotação anterior preservada.")

req=urllib.request.Request(
    "https://api.wise.com/v1/rates?source=CNY&target=BRL",
    headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"SalamitoSkins-FX/1.0"}
)
with urllib.request.urlopen(req,timeout=18) as response:
    data=json.load(response)
if not isinstance(data,list) or not data:
    raise RuntimeError("Wise API não retornou uma cotação CNY/BRL válida.")
rate=float(data[0]["rate"])
if not (0.1<rate<3):
    raise RuntimeError("Cotação Wise fora dos limites esperados.")
output={"pair":"CNY/BRL","rate":rate,"source":"Wise API","fetched_at":datetime.now(timezone.utc).isoformat()}
pathlib.Path("fx.json").write_text(json.dumps(output,ensure_ascii=False),encoding="utf-8")
print("Cotação Wise:",rate)

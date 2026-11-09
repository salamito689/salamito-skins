import json, os, pathlib, urllib.request
from datetime import datetime, timezone

def get_json(url, headers=None):
    req=urllib.request.Request(url,headers=headers or {"User-Agent":"SalamitoSkins-FX/1.0"})
    with urllib.request.urlopen(req,timeout=18) as response:
        return json.load(response)

rate=None
source=None
token=os.getenv("WISE_API_TOKEN","").strip()
if token:
    try:
        data=get_json("https://api.wise.com/v1/rates?source=CNY&target=BRL",{"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"SalamitoSkins-FX/1.0"})
        if isinstance(data,list) and data:
            rate=float(data[0]["rate"])
            source="Wise API"
    except Exception as e:
        print("Wise indisponível; tentando fonte alternativa:",str(e)[:160])
if not rate:
    data=get_json("https://open.er-api.com/v6/latest/CNY")
    if data.get("result")!="success":
        raise RuntimeError("Câmbio indisponível")
    rate=float(data["rates"]["BRL"])
    source="ExchangeRate-API (não Wise)"
if not (0.1<rate<3):
    raise RuntimeError("Cotação fora dos limites esperados")
output={"pair":"CNY/BRL","rate":rate,"source":source,"fetched_at":datetime.now(timezone.utc).isoformat()}
pathlib.Path("fx.json").write_text(json.dumps(output,ensure_ascii=False),encoding="utf-8")
print("Câmbio:",rate,"Fonte:",source)

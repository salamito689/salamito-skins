"""Audit catalog coverage without inventing or copying prices across different items."""
import json, pathlib, urllib.request
from collections import Counter
from datetime import datetime, timezone

catalog_url="https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/all.json"
with urllib.request.urlopen(urllib.request.Request(catalog_url,headers={"User-Agent":"SalamitoSkins/1.0"}),timeout=70) as response:
    catalog=json.load(response)
prices=json.loads(pathlib.Path("prices.json").read_text(encoding="utf-8"))
known=prices["prices"]
phase=prices.get("phase_prices",{})
groups=Counter()
missing=Counter()
examples={}
if isinstance(catalog,dict):
    catalog=list(catalog.values())
if not isinstance(catalog,list) or len(catalog)<1000:
    raise RuntimeError("Catálogo inesperado; auditoria não publicada")
for item in catalog:
    if not isinstance(item,dict):continue
    name=item.get("market_hash_name") or item.get("name") or ""
    if not name:continue
    item_id=str(item.get("id") or "").lower()
    if item_id.startswith("key-"):continue
    if item_id.startswith("sticker-") or "sticker slab" in name.lower():category="Adesivos"
    elif item_id.startswith("agent-"):category="Agentes"
    elif item_id.startswith(("keychain-","charm-")):category="Chaveiros"
    elif item_id.startswith(("crate-","container-")):category="Caixas e cápsulas"
    elif item_id.startswith("patch-"):category="Patches"
    elif item_id.startswith("graffiti-"):category="Grafites"
    elif item_id.startswith(("music_kit-","music-kit-")):category="Kits de música"
    elif item_id.startswith(("skin-","weapon-")):
        lower=name.lower()
        category="Facas" if any(x in lower for x in ("knife","bayonet","karambit","dagger","falchion","talon")) else ("Luvas" if any(x in lower for x in ("glove","wraps")) else "Armas e skins")
    else:category="Outros"
    groups[category]+=1
    record=known.get(name)
    has_price=isinstance(record,dict) and isinstance(record.get("cny"),(int,float)) and record["cny"]>0
    # Doppler phases require their own independent phase quote; a generic quote is insufficient.
    if "doppler" in name.lower() and any(t in name for t in ("Phase 1","Phase 2","Phase 3","Phase 4","Ruby","Sapphire","Black Pearl","Emerald")):
        variant=next((t for t in ("Phase 1","Phase 2","Phase 3","Phase 4","Ruby","Sapphire","Black Pearl","Emerald") if t in name),None)
        has_price=bool(phase.get(name,{}).get(variant,{}).get("cny"))
    if not has_price:
        missing[category]+=1
        examples.setdefault(category,[])
        if len(examples[category])<15:examples[category].append(name)
if sum(groups.values())<1000:
    raise RuntimeError("Auditoria vazia; não sobrescrever relatório anterior")
report={"generated_at":datetime.now(timezone.utc).isoformat(),"note":"Diagnostic based on exact catalog names; categories are approximate and may include items hidden in storefront. Missing does not mean unavailable on YouPin.","total_checked":sum(groups.values()),"total_missing":sum(missing.values()),"categories":{k:{"checked":v,"missing":missing[k],"priced":v-missing[k],"examples_missing":examples.get(k,[])} for k,v in sorted(groups.items())}}
pathlib.Path("price-coverage.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("Coverage:",report["total_checked"],"missing:",report["total_missing"])

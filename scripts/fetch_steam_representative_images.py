"""Fetch representative CS2 model icons from Steam Community Market for staging.
Images are MODEL references, never exact SKU screenshots. Fail closed on mismatches.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE=Path("uuskins-prices-brl-staging.json")
OUTPUT=Path("representative-images/manifest.json")
MAX_BYTES=2_000_000

def fetch_icon(model):
    params=urllib.parse.urlencode({"query":model,"start":0,"count":10,"search_descriptions":0,
                                    "sort_column":"popular","sort_dir":"desc","appid":730,"norender":1})
    req=urllib.request.Request("https://steamcommunity.com/market/search/render/?"+params,
        headers={"User-Agent":"Mozilla/5.0 SalamitoSkinsStaging/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=15) as response:
        payload=json.load(response)
    for result in payload.get("results",[]):
        if not isinstance(result,dict) or result.get("hash_name")!=model:
            continue
        asset=result.get("asset_description") or {}
        icon=asset.get("icon_url_large") or asset.get("icon_url")
        if isinstance(icon,str) and re.fullmatch(r"[A-Za-z0-9_/-]{20,600}",icon):
            return "https://community.fastly.steamstatic.com/economy/image/"+icon
    return None

def main():
    payload=json.loads(SOURCE.read_text(encoding="utf-8"))
    if payload.get("simulation_only") is not True or payload.get("checkout_enabled") is not False:
        raise ValueError("Staging-only simulation required")
    models=sorted({x["market_hash_name"] for x in payload["listings"]})
    OUTPUT.parent.mkdir(exist_ok=True)
    icons={}
    for model in models:
        try:
            url=fetch_icon(model)
            if url:
                icons[model]=url
                print("Found exact-model representative icon:",model)
            else:
                print("No matching model icon:",model)
        except Exception as exc:
            print("Steam image lookup unavailable for",model,type(exc).__name__)
        time.sleep(0.4)
    OUTPUT.write_text(json.dumps({"schema_version":1,"source":"Steam Community Market model icons",
        "representative_only":True,"images":icons},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Representative model images:",len(icons),"/",len(models))

if __name__=="__main__":
    main()

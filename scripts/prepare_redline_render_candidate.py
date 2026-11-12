"""Prepare a real UUSKINS AK-47 Redline for a no-subscription render experiment.
Read-only. Never publish a generic image as an exact listing render.
"""
import hashlib
import json
import re
from pathlib import Path

SRC=Path("uuskins-sku-preview.json")
OUT=Path("uuskins-redline-render-candidate.json")

def main():
    data=json.loads(SRC.read_text(encoding="utf-8"))
    matches=[]
    for group in data.get("results",[]):
        if group.get("market_hash_name")!="AK-47 | Redline (Field-Tested)":
            continue
        for item in group.get("sample_listings",[]):
            code=item.get("inspect_embed_code")
            if not isinstance(code,str) or not re.fullmatch("[A-Fa-f0-9]{24,4096}",code) or len(code)%2:
                continue
            matches.append(item)
    if not matches:
        raise SystemExit("No self-contained inspect hex found for AK-47 Redline")
    item=matches[0]
    code=item["inspect_embed_code"].upper()
    result={
      "model":"AK-47 | Redline (Field-Tested)",
      "listing_id":str(item.get("id") or item.get("skuId") or item.get("sku_id") or ""),
      "float":item.get("wearValue"),
      "pattern":item.get("paintSeed"),
      "paint_index":item.get("paintIndex"),
      "inspect_hex":code,
      "inspect_sha256":hashlib.sha256(code.encode("ascii")).hexdigest(),
      "candidate_renderer":"self-hosted / locally captured CS2 image, not yet implemented",
      "image_generated":False,
      "exactness_verified":False,
      "approved_for_public_catalog":False,
      "note":"Use this actual listing as render input. Verify stickers, charms, float and pattern before accepting any image."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Prepared one real AK-47 Redline candidate; inspect hex validated; no image claimed.")
if __name__=="__main__":
    main()

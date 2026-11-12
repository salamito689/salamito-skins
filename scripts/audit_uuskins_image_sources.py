"""Audit UUSKINS listing image fields without exposing listing IDs or inspect URLs.
Read-only; does not infer that a catalog icon is an exact-item screenshot.
"""
import json
from pathlib import Path
from collections import Counter

SOURCE=Path("uuskins-sku-preview.json")
OUT=Path("uuskins-image-source-audit.json")

def main():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    counts=Counter()
    examples=[]
    for group in data.get("results", []):
        for item in group.get("sample_listings", []):
            counts["listings_examined"]+=1
            fields=item.get("image_field_diagnostics", [])
            if fields:
                counts["listings_with_image_candidate"]+=1
                for field in fields:
                    counts["field:"+str(field.get("field"))]+=1
                    if len(examples)<12:
                        examples.append({"field":field.get("field"),"https_url":field.get("https_url"),"host":field.get("host")})
            if item.get("inspect_available"):
                counts["inspect_links_available"]+=1
    result={"source":"UUSKINS individual SKU read-only sample","counts":dict(counts),
            "image_field_examples":examples,"exact_image_verified":False,
            "note":"Model icons are not exact-listing screenshots. No source images published.",
            "checkout_enabled":False}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("UUSKINS_IMAGE_SOURCE_AUDIT "+json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()

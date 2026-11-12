"""Validate a manually captured exact CS2 screenshot before admitting it to staging.
A screenshot is never automatically trusted: the operator must explicitly attest
that the inspect link, listing ID, float, pattern, stickers and charms match.
No paid API, no scraping, no production publishing.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",default="uuskins-redline-render-candidate.json")
    p.add_argument("--image",required=True)
    p.add_argument("--attest-exact",action="store_true")
    p.add_argument("--output",default="exact-images/manifest.json")
    args=p.parse_args()
    if not args.attest_exact:
        p.error("Manual visual attestation required; never auto-approve a screenshot")
    data=json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    code=data.get("inspect_hex")
    if not code or hashlib.sha256(code.encode("ascii")).hexdigest()!=data.get("inspect_sha256"):
        raise ValueError("Inspect fingerprint mismatch")
    source=Path(args.image)
    with Image.open(source) as im:
        if im.width<400 or im.height<200 or im.width>8192 or im.height>8192:
            raise ValueError("Invalid image dimensions")
        im.verify()
    if source.stat().st_size>2_000_000:
        raise ValueError("Image too large for exact-image manifest")
    destination=Path(args.output)
    destination.parent.mkdir(parents=True,exist_ok=True)
    filename=str(data["listing_id"])+".webp"
    if not filename[:-5].replace("_","").replace("-","").isalnum():
        raise ValueError("Invalid listing ID")
    from PIL import Image as PILImage
    with PILImage.open(source) as im:
        im.convert("RGB").save(destination.parent/filename,format="WEBP",quality=90)
    manifest={"schema_version":1,"images":[{
      "source":"UUSKINS","listing_id":str(data["listing_id"]),
      "file":filename,"inspect_sha256":data["inspect_sha256"]
    }]}
    destination.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("One manually attested exact image prepared for staging only.")

if __name__=="__main__":
    main()

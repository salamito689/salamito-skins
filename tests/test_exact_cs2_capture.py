"""Offline regression tests: synthetic screenshots NEVER count as exact CS2 renders."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"accept_exact_cs2_capture.py"

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        code="AB"*32
        self.candidate=self.dir/"candidate.json"
        self.candidate.write_text(json.dumps({"listing_id":"test_123","inspect_hex":code,
            "inspect_sha256":hashlib.sha256(code.encode()).hexdigest()}))
        self.img=self.dir/"synthetic.png"
        Image.new("RGB",(600,300),"gray").save(self.img)
        self.manifest=self.dir/"exact-images"/"manifest.json"

    def run_script(self,*extra):
        return subprocess.run([sys.executable,str(SCRIPT),"--candidate",str(self.candidate),
            "--image",str(self.img),"--output",str(self.manifest),*extra],
            capture_output=True,text=True)

    def test_no_attestation_rejected(self):
        r=self.run_script()
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.manifest.exists())

    def test_wrong_fingerprint_rejected(self):
        data=json.loads(self.candidate.read_text())
        data["inspect_sha256"]="0"*64
        self.candidate.write_text(json.dumps(data))
        r=self.run_script("--attest-exact")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.manifest.exists())

    def test_invalid_image_rejected(self):
        self.img.write_bytes(b"not an image")
        r=self.run_script("--attest-exact")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.manifest.exists())

    def test_synthetic_image_only_tests_pipeline(self):
        r=self.run_script("--attest-exact")
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(self.manifest.read_text())
        self.assertEqual(data["images"][0]["listing_id"],"test_123")
        self.assertTrue((self.manifest.parent/"test_123.webp").is_file())
        # This is a software test only. The test image is NOT a CS2 item.

if __name__=="__main__":
    unittest.main()

"""Static safety and layout regression checks for the staging catalog.
No external APIs, purchases, or production deployment.
"""
import re
import unittest
from pathlib import Path

HTML = Path("catalogo.html").read_text(encoding="utf-8")

class CatalogLayoutTests(unittest.TestCase):
    def test_five_columns_and_responsive_layout(self):
        self.assertIn("@media(min-width:1200px){.catalog-results .grid{grid-template-columns:repeat(5,minmax(0,1fr))}}", HTML)
        self.assertIn("repeat(4,minmax(0,1fr))", HTML)
        self.assertIn("repeat(3,minmax(0,1fr))", HTML)

    def test_art_is_centered_and_no_vertical_offset(self):
        self.assertIn("object-position:center bottom", HTML)
        self.assertIn(".catalog-results .item.rarity-item .art{margin:0;width:100%", HTML)
        self.assertNotIn("transform:none;margin:auto;padding:9px", HTML)

    def test_local_preview_loads_published_price_files(self):
        self.assertIn('const PREVIEW_LOCAL=location.protocol==="file:"', HTML)
        self.assertIn('PREVIEW_DATA_BASE+"prices.json"', HTML)
        self.assertIn('PREVIEW_DATA_BASE:"")+"fx.json', HTML)

    def test_price_labels_not_repeated(self):
        self.assertNotIn("Referência Buff163", HTML)
        self.assertNotIn("Preço estimado Salamito", HTML)
        self.assertIn("Catálogo em fase de testes", HTML)
        self.assertIn("Cotação desatualizada · confirmar antes da compra", HTML)

    def test_low_liquidity_warning_kept(self):
        self.assertIn("Atenção: item possivelmente com baixa liquidez.", HTML)

    def test_no_unverified_checkout_claims(self):
        self.assertIn("Nenhum pagamento é processado nesta página.", HTML)

if __name__ == "__main__":
    unittest.main()

# UUSKINS integration — safe staging

Branch: `feature/uuskins-safe-integration`. The live site on `main` is untouched.

## Current state
- Read-only market-list probe implemented in `scripts/test_uuskins.py`.
- Does **not** modify `catalogo.html`, `prices.json`, `fx.json`, the cart, or any scheduled workflow.
- Does not place credentials or the RSA private key in repository files.
- Does not create orders or make purchases.
- The script only writes `uuskins-preview.json` after a successful API response.
- API approval, response currency, pricing units, rate limits, data freshness, and coverage must be validated before promotion.

## Verified read-only API results (2026-11-11)
- Manual workflow succeeded and exported 20 sample items.
- Endpoint: `POST /api/vertex/commodity/query/market/openapi/list`.
- Top-level keys: `code`, `data`, `msg`, `timestamp`; `data` contains `items`.
- Each market item exposes `market_hash_name`, `min_price`, `count`, `link`.
- No currency or unit hint in top-level or data response; **never convert min_price to BRL before validating currency and units**.
- This response does not expose float, paint seed, asset ID, listing ID or per-listing price.
- Further endpoint discovery must use verified UUSKINS documentation; do not guess signed API routes or attempt purchases.
- Keep production `prices.json`, `fx.json`, `catalogo.html` and workflows unchanged until validation.

## Requirements
- Python 3.12+ with `cryptography` installed.
- `UUSKINS_APP_KEY` and `UUSKINS_PRIVATE_KEY_PEM` supplied securely as environment variables (prefer GitHub Actions secrets or a local protected environment).
- Never paste the private key in chat, workflow YAML, a commit, or a publicly visible page.

## Validation checklist
1. Confirm the app's permission is active.
2. Execute read-only probe and verify the returned market list.
3. Compare actual UUSKINS prices against the site and UUSKINS website for several items, including Doppler phases.
4. Confirm currency/units and allowed polling interval.
5. Implement a separately generated data feed with automatic fallback to OpenSkin.
6. Only after validation, deploy a tested change to `main`.

## Rollback
No production rollback is necessary until staging is promoted: `main` and the live catalog remain unchanged.

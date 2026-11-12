param(
  [Parameter(Mandatory=$true)][string]$Candidate,
  [Parameter(Mandatory=$true)][string]$Screenshot,
  [switch]$ConfirmExact
)
$ErrorActionPreference = "Stop"
# This workflow uses the user's installed Steam/CS2. It does not manipulate
# game memory, inject code, or claim a screenshot was automatically rendered.
$data = Get-Content -Raw -LiteralPath $Candidate | ConvertFrom-Json
if ($data.model -ne "AK-47 | Redline (Field-Tested)") { throw "Unexpected item model" }
if ($data.inspect_hex -notmatch '^[A-Fa-f0-9]{24,4096}$' -or ($data.inspect_hex.Length % 2) -ne 0) {
  throw "Invalid inspect payload"
}
$sha = [System.Security.Cryptography.SHA256]::Create()
try { $hashBytes = $sha.ComputeHash([Text.Encoding]::ASCII.GetBytes($data.inspect_hex)) }
finally { $sha.Dispose() }
$hash = ([BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
if ($hash -ne $data.inspect_sha256) { throw "Inspect payload fingerprint mismatch" }
$inspectUrl = "steam://run/730//+csgo_econ_action_preview%20A$($data.inspect_hex)"
Write-Host "Opening the exact UUSKINS item in Steam / CS2..."
Start-Process $inspectUrl
Write-Host "Inspect the item visually, including stickers and charms."
Write-Host "Save a genuine screenshot to: $Screenshot"
Read-Host "After saving the screenshot, press Enter"
if (-not (Test-Path -LiteralPath $Screenshot -PathType Leaf)) { throw "Screenshot not found" }
if (-not $ConfirmExact) {
  Write-Host "Not attested. Run again with -ConfirmExact ONLY after manually verifying exact item."
  exit 2
}
python -m pip install Pillow
python scripts/accept_exact_cs2_capture.py --candidate $Candidate --image $Screenshot --attest-exact
if ($LASTEXITCODE -ne 0) { throw "Image validation failed" }
Write-Host "Exact capture accepted into local staging only; no public upload."

<#
Run the full pipeline: optional PRADAN download, combine, nowcast detect, label, train.

Usage (PowerShell, from repo root):
  & .\run_full_pipeline.ps1

Environment:
  - Activate your venv first: & .\.venv\Scripts\Activate.ps1
  - If you want to download from PRADAN, set `PRADAN_COOKIE` and create `pradan_urls.txt`.

This script will NOT push to GitHub.
#>
param()

Write-Host "Running full pipeline..."

if (Test-Path pradan_urls.txt) {
    if (-not $env:PRADAN_COOKIE) {
        Write-Host "PRADAN urls present but PRADAN_COOKIE not set. Skipping download." -ForegroundColor Yellow
    } else {
        Write-Host "Running PRADAN downloader..."
        bash pradan_bulk_download.sh
    }
} else {
    Write-Host "No pradan_urls.txt found - skipping download." -ForegroundColor Yellow
}

Write-Host "Combining SoLEXS zips..."
python "Solar Low Energy X-ray Spectrometer/scripts/combine_solexs.py"

Write-Host "Running SoLEXS nowcast detection..."
python "Solar Low Energy X-ray Spectrometer/scripts/generate_solexs_nowcast.py"

Write-Host "Labeling SoLEXS with external catalogs..."
python "Solar Low Energy X-ray Spectrometer/scripts/label_flares.py"

Write-Host "Training leakage-free forecaster (Single Instrument)..."
python scripts/train_forecast_sklearn.py

Write-Host "Training leakage-free forecaster (Dual-Instrument Fusion)..."
python scripts/train_forecast_dual_fusion.py

Write-Host "Pipeline finished. Check output/ for artifacts." -ForegroundColor Green

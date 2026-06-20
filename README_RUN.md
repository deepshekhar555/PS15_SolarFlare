# Running the full pipeline

Quick steps to run the full ingest → detection → labeling → training pipeline locally.

1) Activate your virtual environment (PowerShell):
```powershell
& .\.venv\Scripts\Activate.ps1
```

2) (Optional) If you need PRADAN archival data:
- Put one download URL per line into `pradan_urls.txt` in the repo root.
- Export your PRADAN cookie (PowerShell):
```powershell
$env:PRADAN_COOKIE = 'session=...; other=...'
```

3) Run the unified pipeline (PowerShell):
```powershell
& .\run_full_pipeline.ps1
```

Outputs will be written to the `output/` folder. The script will not push anything to GitHub.

If you prefer Git Bash you can still run the same Python commands manually — the script is a convenience wrapper.

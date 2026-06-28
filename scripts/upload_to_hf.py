#!/usr/bin/env python3
"""
Automated Dataset Uploader for Hugging Face Hub.
This script packages and uploads the raw, processed, or zipped Aditya-L1 solar flare dataset
to the Hugging Face Hub.
"""

import os
import sys
import getpass
from pathlib import Path

def check_dependencies():
    try:
        import huggingface_hub
        from huggingface_hub import HfApi
        return True
    except ImportError:
        print("\n=== Missing Dependency ===")
        print("The 'huggingface_hub' package is required to upload datasets.")
        print("Please install it by running:")
        print("  pip install huggingface_hub")
        print("==========================\n")
        return False

def main():
    # Configure stdout to use UTF-8 if supported, to avoid encoding issues
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=========================================================")
    print("Aditya-L1 Solar Flare Dataset Uploader to Hugging Face")
    print("=========================================================")

    if not check_dependencies():
        sys.exit(1)

    from huggingface_hub import HfApi

    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent

    # Define paths
    raw_solexs = project_root / "Solar Low Energy X-ray Spectrometer" / "data"
    raw_hel1os = project_root / "High Energy L1 Orbiting X-ray Spectrometer" / "data"
    processed_dir = project_root / "output"
    workspace_zip = project_root / "PS15_SolarFlare.zip"

    # 1. Choose what to upload
    print("\nSelect what you want to upload:")
    print("1) Processed & ML-Ready Dataset (Outputs, Catalogs, and Models - ~50MB)")
    print("2) Raw Telemetry Dataset (Full SoLEXS and HEL1OS FITS/ZIP files - ~900MB)")
    print("3) Entire Project ZIP Package (Includes both code and data - ~890MB)")
    print("4) All of the above")
    
    choice = input("\nEnter choice (1-4, default 1): ").strip() or "1"
    
    uploads = []
    if choice == "1":
        uploads.append(("folder", processed_dir, "processed_output"))
    elif choice == "2":
        uploads.append(("folder", raw_solexs, "raw_data/solexs"))
        uploads.append(("folder", raw_hel1os, "raw_data/hel1os"))
    elif choice == "3":
        if not workspace_zip.exists():
            print(f"\n[ERROR] Workspace ZIP not found at {workspace_zip}")
            print("Please run the zip script first:")
            print("  python zip_workspace.py")
            sys.exit(1)
        uploads.append(("file", workspace_zip, "PS15_SolarFlare.zip"))
    elif choice == "4":
        uploads.append(("folder", processed_dir, "processed_output"))
        uploads.append(("folder", raw_solexs, "raw_data/solexs"))
        uploads.append(("folder", raw_hel1os, "raw_data/hel1os"))
        if workspace_zip.exists():
            uploads.append(("file", workspace_zip, "PS15_SolarFlare.zip"))
    else:
        print("[ERROR] Invalid choice. Exiting.")
        sys.exit(1)

    # 2. Authenticate
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("\nHF_TOKEN environment variable not found.")
        print("To upload, you need a Hugging Face Access Token with WRITE permissions.")
        print("Get your token here: https://huggingface.co/settings/tokens")
        token = getpass.getpass("Enter your Hugging Face WRITE Token: ").strip()

    if not token:
        print("[ERROR] No token provided. Exiting.")
        sys.exit(1)

    # Initialize Hugging Face API
    api = HfApi(token=token)

    # 3. Get Repository ID
    default_user = ""
    try:
        user_info = api.whoami()
        default_user = user_info.get("name", "")
        print(f"\nAuthenticated successfully as: {default_user}")
    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        print("Please verify that your write token is correct.")
        sys.exit(1)

    default_repo = f"{default_user}/aditya-l1-solar-flare"
    repo_id = input(f"Enter target repository ID (default '{default_repo}'): ").strip() or default_repo

    # 4. Public or Private
    is_private_input = input("Make the repository private? (y/n, default n): ").strip().lower()
    private = is_private_input == "y" or is_private_input == "yes"

    # Create dataset repository
    print(f"\nCreating/Verifying Hugging Face Dataset repository '{repo_id}'...")
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            private=private,
            exist_ok=True
        )
        print("[SUCCESS] Repository ready.")
    except Exception as e:
        print(f"[ERROR] Error creating repository: {e}")
        sys.exit(1)

    # 5. Perform uploads
    print("\nStarting upload. Please wait, this may take several minutes for large files...")
    
    for upload_type, local_path, path_in_repo in uploads:
        if upload_type == "folder":
            print(f"[INFO] Uploading folder '{local_path.name}' to '{path_in_repo}'...")
            try:
                api.upload_folder(
                    folder_path=str(local_path),
                    path_in_repo=path_in_repo,
                    repo_id=repo_id,
                    repo_type="dataset",
                    ignore_patterns=[".git*", "*.pyc", "__pycache__"]
                )
                print(f"[SUCCESS] Folder '{local_path.name}' uploaded successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to upload folder '{local_path.name}': {e}")
        
        elif upload_type == "file":
            print(f"[INFO] Uploading file '{local_path.name}' to '{path_in_repo}'...")
            try:
                api.upload_file(
                    path_or_fileobj=str(local_path),
                    path_in_repo=path_in_repo,
                    repo_id=repo_id,
                    repo_type="dataset"
                )
                print(f"[SUCCESS] File '{local_path.name}' uploaded successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to upload file '{local_path.name}': {e}")

    # 6. Generate Dataset Card
    print("\n[INFO] Generating a basic Dataset Card (README.md) on Hugging Face...")
    readme_content = f"""---
title: Aditya-L1 Solar Flare Dataset
emoji: ☀️
colorFrom: yellow
colorTo: orange
sdk: static
pinned: false
license: cc-by-4.0
task_categories:
- time-series-forecasting
- tabular-classification
tags:
- space-weather
- solar-flare
- aditya-l1
- fits
---

# Aditya-L1 Space Weather and Solar Flare Dataset

An end-to-end dataset for space weather monitoring and forecasting using raw and processed X-ray flux data from ISRO's **Aditya-L1** space observatory. 

Developed by team **SolarSentinels** (Adamas University, Kolkata) for the ISRO Aditya-L1 Hackathon.

## Repository Contents

This repository contains the dataset structures used in the Solar Flare Nowcasting & Forecasting System:

- **`processed_output/`**: Merged, synchronized multi-instrument time series data, nowcast event catalogs, and trained model objects.
- **`raw_data/`**: Raw telemetry count rates from the **SoLEXS** and **HEL1OS** instruments (FITS and ZIP formats).
- **`PS15_SolarFlare.zip`**: The complete workspace zip package containing all project code, configurations, and data.

## Loading the Dataset in Python

To download and load the processed time series or event catalog using pandas:

```python
import pandas as pd

# Load the combined nowcast catalog
catalog_url = "https://huggingface.co/datasets/{repo_id}/raw/main/processed_output/solexs_hel1os_combined_catalog.csv"
df_catalog = pd.read_csv(catalog_url)
print(df_catalog.head())
```

For more details, visit the official code repository: [GitHub Link](https://github.com/deepshekhar555/PS15_SolarFlare)
"""
    try:
        api.upload_file(
            path_or_fileobj=readme_content.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset"
        )
        print("[SUCCESS] Dataset Card generated successfully.")
    except Exception as e:
        print(f"[WARNING] Could not upload Dataset Card: {e}")

    print("\n[SUCCESS] ALL UPLOADS COMPLETED.")
    print(f"Your dataset is now available at: https://huggingface.co/datasets/{repo_id}")
    print("=========================================================")

if __name__ == "__main__":
    main()

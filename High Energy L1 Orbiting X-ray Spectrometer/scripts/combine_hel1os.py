#!/usr/bin/env python3
"""Combine HEL1OS lightcurve FITS files into one CSV."""
import os
import zipfile
import shutil
import glob
from astropy.io import fits
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import gc
import time

# ===== SETTINGS =====
ROOT = Path(__file__).resolve().parents[1]
DATA_FOLDER = ROOT / 'data'
OUTPUT_CSV = ROOT / 'output' / 'hel1os_combined.csv'
TEMP_FOLDER = ROOT / 'output' / 'temp'

OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

zip_files = list(DATA_FOLDER.glob('*.zip'))
print(f'Found {len(zip_files)} HEL1OS zip files')

all_data = []


def mjd_to_unix(mjd):
    """Convert Modified Julian Date to Unix timestamp."""
    # MJD 0 = 1858-11-17 00:00 UTC
    # Unix epoch = 1970-01-01 00:00 UTC
    # Difference: 40587 days
    mjd_epoch = 40587.0
    unix_time = (mjd - mjd_epoch) * 86400.0
    return unix_time


def process_hel1os_zip(zip_path, temp_folder):
    """Extract and process all HEL1OS data from a nested zip structure."""
    local_data = []
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        nested_zips = [m for m in z.namelist() if m.endswith('.zip')]
        print(f'  Found {len(nested_zips)} nested zips')
        
        for nested_name in nested_zips:
            nested_data = z.read(nested_name)
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp.write(nested_data)
                tmp_path = tmp.name
            
            try:
                with zipfile.ZipFile(tmp_path, 'r') as z2:
                    # Find lightcurve FITS files
                    lc_fits = [m for m in z2.namelist() if 'lightcurve_' in m and m.endswith('.fits')]
                    
                    for lc_file in lc_fits:
                        lc_data = z2.read(lc_file)
                        with tempfile.NamedTemporaryFile(suffix='.fits', delete=False) as tmp2:
                            tmp2.write(lc_data)
                            tmp2_path = tmp2.name
                        
                        try:
                            with fits.open(tmp2_path) as hdul:
                                # Use broadest energy band (18-160 keV) for consistency
                                target_ext = None
                                for ext in hdul[1:]:
                                    if '18.00KEV_TO_160.00KEV' in (ext.name or ''):
                                        target_ext = ext
                                        break
                                
                                # Fallback: use first data extension if broadest not found
                                if target_ext is None and len(hdul) > 1:
                                    target_ext = hdul[1]
                                
                                if target_ext is not None and target_ext.data is not None:
                                    mjd = target_ext.data['MJD']
                                    ctr = target_ext.data['CTR']
                                    
                                    # Convert MJD to Unix timestamp
                                    time_unix = mjd_to_unix(mjd)
                                    
                                    df = pd.DataFrame({'TIME': time_unix, 'COUNTS': ctr})
                                    # Convert Unix timestamp to date string
                                    df['DATETIME'] = pd.to_datetime(df['TIME'], unit='s', origin='unix', utc=True)
                                    df['DATE'] = df['DATETIME'].dt.strftime('%Y%m%d')
                                    df = df.drop(columns=['DATETIME'])
                                    local_data.append(df)
                        except Exception as e:
                            print(f'    Error processing {lc_file}: {e}')
                        finally:
                            gc.collect()
                            time.sleep(0.1)
                            try:
                                Path(tmp2_path).unlink()
                            except:
                                pass
            finally:
                gc.collect()
                time.sleep(0.1)
                try:
                    Path(tmp_path).unlink()
                except:
                    pass
    
    return local_data


for idx, zip_path in enumerate(zip_files):
    try:
        print(f'Processing {zip_path.name}...')
        data = process_hel1os_zip(zip_path, TEMP_FOLDER)
        all_data.extend(data)
        print(f'✅ Done {idx+1}/{len(zip_files)}: {zip_path.name}')
    except Exception as e:
        print(f'❌ Error in {zip_path.name}: {e}')

if not all_data:
    print('No HEL1OS data was combined.')
else:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df = final_df.dropna(subset=['COUNTS'])
    final_df = final_df.sort_values('TIME').reset_index(drop=True)

    # Aggregate multiple counts at same time (sum across detectors to preserve signal)
    final_df = final_df.groupby('TIME', as_index=False).agg({
        'COUNTS': 'sum',
        'DATE': 'first'
    })

    print(f'\nTotal data points: {len(final_df):,}')
    print(f'Date range: {final_df["DATE"].min()} to {final_df["DATE"].max()}')

    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f'\n✅ Saved to: {OUTPUT_CSV}')

if TEMP_FOLDER.exists():
    shutil.rmtree(TEMP_FOLDER)
    print('✅ Temp files cleaned up!')

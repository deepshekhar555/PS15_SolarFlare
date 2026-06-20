import os
import zipfile
import gzip
import shutil
import glob
from astropy.io import fits
import pandas as pd
import numpy as np

# ===== SETTINGS =====
DATA_FOLDER = "D:/PS15_SolarFlare/data/solexs"
OUTPUT_CSV = "D:/PS15_SolarFlare/output/solexs_combined.csv"
TEMP_FOLDER = "D:/PS15_SolarFlare/output/temp"

os.makedirs(TEMP_FOLDER, exist_ok=True)

zip_files = glob.glob(os.path.join(DATA_FOLDER, "AL1_SLX_L1_*.zip"))
print(f"Found {len(zip_files)} zip files")

all_data = []

for idx, zip_path in enumerate(zip_files):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for name in z.namelist():
                if name.endswith('.lc.gz'):
                    z.extract(name, TEMP_FOLDER)
                    gz_path = os.path.join(TEMP_FOLDER, name)
                    fits_path = gz_path.replace('.gz', '')

                    with gzip.open(gz_path, 'rb') as f_in:
                        with open(fits_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    hdul = fits.open(fits_path)
                    t = hdul[1].data['TIME']
                    c = hdul[1].data['COUNTS']
                    hdul.close()

                    fname = os.path.basename(zip_path)
                    date_str = fname.split('_')[3]

                    df = pd.DataFrame({'TIME': t, 'COUNTS': c})
                    df['DATE'] = date_str
                    all_data.append(df)

        print(f"✅ Done {idx+1}/{len(zip_files)}: {os.path.basename(zip_path)}")

    except Exception as e:
        print(f"❌ Error in {zip_path}: {e}")

print("\nCombining all data...")
final_df = pd.concat(all_data, ignore_index=True)
final_df = final_df.dropna(subset=['COUNTS'])

print(f"Total data points: {len(final_df)}")
print(f"Date range: {final_df['DATE'].min()} to {final_df['DATE'].max()}")

final_df.to_csv(OUTPUT_CSV, index=False)
print(f"\n✅ Saved to: {OUTPUT_CSV}")

shutil.rmtree(TEMP_FOLDER)
print("✅ Temp files cleaned up!")
"""Fetch GOES xray event list for a given year (best-effort).
Saves to data/goes_xray_{year}.txt if successful.
"""
import os
import urllib.request
from pathlib import Path
import sys

year = sys.argv[1] if len(sys.argv) > 1 else '2026'
paths = [
    f"https://www.ngdc.noaa.gov/stp/space-weather/solar-data/solar-features/solar-flares/goes/goes_xray_{year}.txt",
    f"https://www.ngdc.noaa.gov/stp/space-weather/solar-data/solar-features/solar-flares/goes_xray_{year}.txt",
    f"https://ngdc.noaa.gov/STP/space-weather/solar-data/solar-features/solar-flares/goes/goes_xray_{year}.txt",
    f"https://ngdc.noaa.gov/stp/solar/onlinepubs/solaralerts/goes_xray_{year}.txt",
]

out_dir = Path('D:/PS15_SolarFlare/data')
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / f'goes_xray_{year}.txt'

for url in paths:
    try:
        print(f'Trying: {url}')
        with urllib.request.urlopen(url, timeout=20) as r:
            content = r.read()
            if len(content) > 100:  # basic sanity
                out_file.write_bytes(content)
                print(f'Downloaded {url} -> {out_file}')
                sys.exit(0)
    except Exception as e:
        print(f'Failed: {e}')

print('All attempts failed. Please provide a direct URL.')
sys.exit(1)

"""Fetch small, lightweight solar event lists and a Helioviewer sample image.
This script avoids large archives; it downloads only small text files or a single JPG sample.
"""
import urllib.request
from pathlib import Path

ROOT = Path('D:/PS15_SolarFlare')
DATA = ROOT / 'data'
DATA.mkdir(parents=True, exist_ok=True)

# RHESSI / HESSI flare catalog URL (valid archive URL discovered during validation)
rhessi_urls = [
    'https://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.txt',
    'https://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.dat',
]

# Fermi / GBM solar flare catalog attempts (public mirror URLs are not stable; use local file if available)
fermi_urls = [
    'https://fermi.gsfc.nasa.gov/ssc/data/access/gbm/solar/flare_list.txt',
    'https://gammaray.msfc.nasa.gov/gbm/trigger_history.txt',
]

# Helioviewer sample image endpoint for a small demo image
hv_render = 'https://api.helioviewer.org/v2/renderImage/?date=2026-06-06T12:00:00Z&source=SDO_AIA_171&size=1024'

out_files = []


def try_download(url, out_path):
    try:
        print('Trying', url)
        with urllib.request.urlopen(url, timeout=20) as r:
            content = r.read()
            if content and len(content) > 50:
                out_path.write_bytes(content)
                print('Saved', out_path)
                return True
    except Exception as e:
        print('Failed', url, e)
    return False

# RHESSI / HESSI
for u in rhessi_urls:
    out = DATA / 'rhessi_flare_list.txt'
    if try_download(u, out):
        out_files.append(out)
        break

# Fermi / GBM
for u in fermi_urls:
    out = DATA / 'fermi_gbm_flare_list.txt'
    if try_download(u, out):
        out_files.append(out)
        break

# Helioviewer sample image
hv_out = DATA / 'helioviewer_sample.jpg'
try_download(hv_render, hv_out)

print('\nDownloaded files:')
if out_files:
    for f in out_files:
        print('-', f)
else:
    print('No external event list files were downloaded.')
print('Note: Fermi/GBM public catalog URLs may not be stable. Local event files can still be used if manually obtained.')

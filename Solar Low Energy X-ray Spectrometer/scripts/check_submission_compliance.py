"""Basic compliance checker for submission packaging.
Checks for presence of DATASETS.md, SUBMISSION_NOTICE.md, README.md and that GOES dataset is documented.
Exits with code 0 on success, non-zero on failure.
"""
import sys
from pathlib import Path

root = Path('D:/PS15_SolarFlare')
required_files = ['README.md', 'DATASETS.md', 'SUBMISSION_NOTICE.md']
missing = []
for f in required_files:
    if not (root / f).exists():
        missing.append(f)

reports = []
if missing:
    reports.append(f"Missing required files: {missing}")

# Check DATASETS.md contains GOES URL
datasets = root / 'DATASETS.md'
if datasets.exists():
    content = datasets.read_text()
    if 'ngdc.noaa.gov' not in content and 'NOAA' not in content:
        reports.append('DATASETS.md does not reference NOAA/GOES')
else:
    reports.append('DATASETS.md missing')

# Check local GOES file exists
goes_file = root / 'data' / 'goes_xray_2026.txt'
if not goes_file.exists():
    reports.append('Local GOES file data/goes_xray_2026.txt not found (optional but recommended)')

# Check that README mentions GOES URL
readme = root / 'README.md'
if readme.exists():
    txt = readme.read_text()
    if 'ngdc.noaa.gov' not in txt and 'GOES' not in txt:
        reports.append('README.md does not mention GOES/NOAA')
else:
    reports.append('README.md missing')

if reports:
    print('Compliance check FAILED:')
    for r in reports:
        print('- ' + r)
    sys.exit(2)
else:
    print('Compliance check PASSED: basic files present and GOES attribution found')
    sys.exit(0)

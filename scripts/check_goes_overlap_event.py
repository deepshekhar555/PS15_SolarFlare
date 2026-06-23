from pathlib import Path
import pandas as pd
from datetime import datetime

root = Path('D:/PS15_SolarFlare')
GOES = root / 'backup_verified_20260619' / 'goes_xray_2026.txt'
MERGED = root / 'output' / 'solexs_nowcast_catalog_merged.csv'

# target event: PEAK_COUNTS == 177
m = pd.read_csv(MERGED)
row = m[m['PEAK_COUNTS']==177.0].iloc[0]
start = pd.to_datetime(row['START'])
peak = pd.to_datetime(row['PEAK_TIME'])
end = pd.to_datetime(row['END'])
# make tz-naive for comparison with GOES entries
try:
    if getattr(start, 'tzinfo', None) is not None or getattr(start, 'tz', None) is not None:
        start = start.tz_convert(None)
except Exception:
    try:
        start = start.tz_localize(None)
    except Exception:
        pass
try:
    if getattr(peak, 'tzinfo', None) is not None or getattr(peak, 'tz', None) is not None:
        peak = peak.tz_convert(None)
except Exception:
    try:
        peak = peak.tz_localize(None)
    except Exception:
        pass
try:
    if getattr(end, 'tzinfo', None) is not None or getattr(end, 'tz', None) is not None:
        end = end.tz_convert(None)
except Exception:
    try:
        end = end.tz_localize(None)
    except Exception:
        pass
print('Suspicious merged event:')
print('  START:', start)
print('  PEAK :', peak)
print('  END  :', end)
print('  DURATION_s:', row['DURATION_s'])

# parse GOES file lines
found = []
with open(GOES, 'r', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line:
            continue
        # lines starting with a date begin with digit
        if line[0].isdigit():
            parts = line.split()
            # expect: Date Start Peak End Class ...
            # date could be like 10-Jun-2026 or 10-Jan-2026
            date = parts[0]
            # times: parts[1]=Start, parts[2]=Peak, parts[3]=End
            try:
                tstart = parts[1]
                tpeak = parts[2]
                tend = parts[3]
            except IndexError:
                continue
            # build datetimes
            try:
                dt_start = datetime.strptime(f"{date} {tstart}", "%d-%b-%Y %H:%M")
                dt_peak = datetime.strptime(f"{date} {tpeak}", "%d-%b-%Y %H:%M")
                dt_end = datetime.strptime(f"{date} {tend}", "%d-%b-%Y %H:%M")
            except Exception:
                # try without year (rare)
                try:
                    dt_start = datetime.strptime(f"{date} {tstart}", "%d-%b %H:%M")
                    dt_peak = datetime.strptime(f"{date} {tpeak}", "%d-%b %H:%M")
                    dt_end = datetime.strptime(f"{date} {tend}", "%d-%b %H:%M")
                except Exception:
                    continue
            # convert to pandas Timestamp for tz-naive comparison
            dt_start = pd.to_datetime(dt_start)
            dt_peak = pd.to_datetime(dt_peak)
            dt_end = pd.to_datetime(dt_end)
            # Check overlap
            if (dt_start <= peak <= dt_end) or (start <= dt_peak <= end) or (dt_start <= end <= dt_end) or (start <= dt_start <= end):
                found.append((date, tstart, tpeak, tend, ' '.join(parts[4:])))

print('\nGOES events overlapping or nearby the merged event:')
if not found:
    print('  None found in goes_xray_2026.txt')
else:
    for f in found:
        print(' ', f)

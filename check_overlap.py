import pandas as pd
from pathlib import Path

solexs_root = Path('Solar Low Energy X-ray Spectrometer')
helos_root = Path('High Energy L1 Orbiting X-ray Spectrometer')

solexs = pd.read_csv(solexs_root / 'output' / 'solexs_nowcast_catalog.csv')
helos = pd.read_csv(helos_root / 'output' / 'hel1os_nowcast_catalog.csv')
matched = pd.read_csv(solexs_root / 'output' / 'matched_flares.csv')

# Convert to Unix seconds
solexs['PT'] = pd.to_datetime(solexs['PEAK_TIME']).astype('int64') // 10**9
helos['PT'] = pd.to_numeric(helos['PEAK_TIME'], errors='coerce')
matched['PT'] = pd.to_datetime(matched['PEAK_DT']).astype('int64') // 10**9

# Overlap: Jun 13-17
overlap_start = 1781352000
overlap_end = 1781865600

s_overlap = solexs[(solexs['PT'] >= overlap_start) & (solexs['PT'] <= overlap_end)]
h_overlap = helos[(helos['PT'] >= overlap_start) & (helos['PT'] <= overlap_end)]
m_overlap = matched[(matched['PT'] >= overlap_start) & (matched['PT'] <= overlap_end)]

print("="*70)
print("CROSS-INSTRUMENT OVERLAP ANALYSIS (Jun 13-17)")
print("="*70)
print(f"\nSoLEXS events in overlap: {len(s_overlap)}")
print(f"HEL1OS events in overlap: {len(h_overlap)}")
print(f"NOAA reference in overlap: {len(m_overlap)}")

# Find cross-matches within 2 minutes
matches = 0
for s_idx, s_row in s_overlap.iterrows():
    for h_idx, h_row in h_overlap.iterrows():
        if abs(s_row['PT'] - h_row['PT']) <= 120:
            matches += 1
            print(f"\n✓ Match: SoLEXS {s_row['PEAK_TIME']}")
            print(f"         HEL1OS {h_row['PEAK_TIME']}")
            print(f"         Delta: {abs(s_row['PT'] - h_row['PT']):.0f}s")

print(f"\n{'='*70}")
print(f"Cross-confirmed events: {matches}")
print(f"SoLEXS-only: {len(s_overlap) - matches}")
print(f"HEL1OS-only: {len(h_overlap) - matches}")
print(f"{'='*70}\n")

if matches == 0:
    if len(m_overlap) == 0:
        print("⚠️  DATA LIMITATION: No NOAA reference flares in Jun 13-17 window")
        print("   Cannot validate dual-confirmation (insufficient reference data)")
    else:
        print("❌ No cross-matches despite events from both instruments")
        print(f"   ({len(s_overlap)} SoLEXS + {len(h_overlap)} HEL1OS events)")
else:
    print(f"✅ Dual-confirmation logic WORKS: {matches} cross-confirmed event(s)")

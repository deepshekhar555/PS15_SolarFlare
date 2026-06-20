import pandas as pd

solexs = pd.read_csv('Solar Low Energy X-ray Spectrometer/output/solexs_nowcast_catalog.csv')
helos = pd.read_csv('High Energy L1 Orbiting X-ray Spectrometer/output/hel1os_nowcast_catalog.csv')
matched = pd.read_csv('Solar Low Energy X-ray Spectrometer/output/matched_flares.csv')

# Convert to Unix seconds
solexs['PT'] = pd.to_datetime(solexs['PEAK_TIME']).astype('int64') // 10**9
helos['PT'] = pd.to_numeric(helos['PEAK_TIME'], errors='coerce')
matched['PT'] = pd.to_datetime(matched['PEAK_DT']).astype('int64') // 10**9

# Real overlap: Jun 13 - Jun 16 23:59 UTC
overlap_start = 1781352000  # Jun 13 00:00
overlap_end = 1781606399    # Jun 16 23:59

s_ov = solexs[(solexs['PT'] >= overlap_start) & (solexs['PT'] <= overlap_end)]
h_ov = helos[(helos['PT'] >= overlap_start) & (helos['PT'] <= overlap_end)]
m_ov = matched[(matched['PT'] >= overlap_start) & (matched['PT'] <= overlap_end)]

print("="*70)
print("ACTUAL OVERLAP ANALYSIS: JUN 13–16 (when both instruments had data)")
print("="*70)
print(f"\nSoLEXS data ends:    2026-06-16T23:56:41")
print(f"HEL1OS data starts:  2026-06-13T??:??:??")
print(f"True overlap window: Jun 13–16")
print()
print(f"Events in overlap:")
print(f"  SoLEXS: {len(s_ov)}")
print(f"  HEL1OS: {len(h_ov)}")
print(f"  NOAA reference: {len(m_ov)}")

# Find cross-matches
matches = 0
match_list = []
for s_idx, s_row in s_ov.iterrows():
    for h_idx, h_row in h_ov.iterrows():
        if abs(s_row['PT'] - h_row['PT']) <= 120:  # ±2 min
            matches += 1
            match_list.append((s_row['PEAK_TIME'], h_row['PEAK_TIME'], abs(s_row['PT'] - h_row['PT'])))

print(f"\n[CROSS-MATCHES] (±2 min tolerance)")
print(f"{'='*70}")
print(f"Cross-confirmed events: {matches}")
if matches > 0:
    for s_time, h_time, delta in match_list:
        print(f"  ✓ SoLEXS {s_time}")
        print(f"    HEL1OS {h_time}")
        print(f"    Δt: {delta:.0f}s\n")

print(f"{'='*70}")
print(f"SoLEXS-only: {len(s_ov) - matches}")
print(f"HEL1OS-only: {len(h_ov) - matches}")
print(f"{'='*70}\n")

# Verdict
if matches == 0:
    if len(m_ov) == 0:
        print("⚠️  FINDING: No NOAA reference flares in Jun 13–16")
        print("   No ground-truth flares to validate against")
        print("   Dual-confirmation logic cannot be validated in this window")
    else:
        print(f"⚠️  NOTE: {len(m_ov)} NOAA flares present Jun 13–16")
        print(f"   {len(s_ov)} SoLEXS + {len(h_ov)} HEL1OS events detected")
        print(f"   NO cross-matches suggests different detection sensitivities")
else:
    print(f"✅ SUCCESS: {matches} cross-confirmed event(s)")
    print(f"   Dual-confirmation logic is FUNCTIONAL")

print("="*70)

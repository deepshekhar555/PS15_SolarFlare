import pandas as pd

s = pd.read_csv('Solar Low Energy X-ray Spectrometer/output/solexs_nowcast_catalog.csv')
s['PT'] = pd.to_datetime(s['PEAK_TIME']).astype('int64') // 10**9

print('SoLEXS data coverage:')
print(f'  Earliest: {s["PEAK_TIME"].min()}')
print(f'  Latest:   {s["PEAK_TIME"].max()}')
print()

# Check Jun 13+ (1781352000 Unix) - Jun 16 00:00 UTC (1781606400)
jun13_start = 1781352000
jun16_end = 1781606400
s_jun13 = s[(s['PT'] >= jun13_start) & (s['PT'] <= jun16_end)]
print(f'SoLEXS events Jun 13-16: {len(s_jun13)}')

import pandas as pd
from pathlib import Path

matched = pd.read_csv('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/matched_flares.csv')
combined = pd.read_csv('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv')
nowcast = pd.read_csv('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_nowcast_catalog.csv')

matched['START_DT'] = pd.to_datetime(matched['START_DT'])
matched['END_DT'] = pd.to_datetime(matched['END_DT'])
matched['PEAK_DT'] = pd.to_datetime(matched['PEAK_DT'])
nowcast['PEAK_TIME'] = pd.to_datetime(nowcast['PEAK_TIME'])
combined['DATETIME'] = pd.to_datetime(combined['TIME'], unit='s', origin='unix', utc=True)

missed_m = matched[(matched['CLASS'].str.startswith('M'))]
print('M-CLASS MATCHED FLARES:', len(missed_m))
print(missed_m[['DATE','START','PEAK','END','CLASS']].to_string(index=False))

if not missed_m.empty:
    m = missed_m.iloc[0]
    start = m['START_DT']
    end = m['END_DT']
    print('\nInspecting raw SoLEXS data for this window:')
    print(start, end)
    window = combined[(combined['DATETIME'] >= start) & (combined['DATETIME'] <= end)]
    print('Raw rows:', len(window))
    if len(window) > 0:
        print(window[['DATETIME','TIME','COUNTS']].head(20).to_string(index=False))
        print('...')
        print(window[['DATETIME','TIME','COUNTS']].tail(20).to_string(index=False))
    else:
        print('No raw SoLEXS rows in this window.')

import pandas as pd
from pathlib import Path

base = Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output')
matched = pd.read_csv(base / 'matched_flares.csv')
nowcast = pd.read_csv(base / 'solexs_nowcast_catalog.csv')

matched['START_DT'] = pd.to_datetime(matched['START_DT'])
matched['END_DT'] = pd.to_datetime(matched['END_DT'])
nowcast['PEAK_TIME'] = pd.to_datetime(nowcast['PEAK_TIME'])

# Determine whether each matched flare contains any nowcast peak
caught = []
missed = []
for _, mf in matched.iterrows():
    peak_in_window = any(
        (mf['START_DT'] <= p <= mf['END_DT'])
        for p in nowcast['PEAK_TIME']
    )
    row = mf.to_dict()
    row['CAUGHT'] = peak_in_window
    if peak_in_window:
        caught.append(row)
    else:
        missed.append(row)

# Classify by flare class letter
for group_name, group in [('CAUGHT', caught), ('MISSED', missed)]:
    df = pd.DataFrame(group)
    if df.empty:
        print(f"{group_name}: 0 events")
        continue
    df['CLASS_LETTER'] = df['CLASS'].astype(str).str[0].str.upper()
    counts = df['CLASS_LETTER'].value_counts().sort_index()
    print(f"{group_name} count: {len(df)}")
    print(counts.to_string())
    print('-' * 60)
    print(df[['DATE', 'START', 'END', 'CLASS', 'CLASS_LETTER']].head(10).to_string(index=False))
    print('\n')

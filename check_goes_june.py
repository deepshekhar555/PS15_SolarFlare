import pandas as pd

# Manually parse the GOES file
lines = open('Solar Low Energy X-ray Spectrometer/data/goes_xray_2026.txt').readlines()

# Skip header and parse lines
events = []
for line in lines[4:]:  # Skip first 4 lines of header
    if not line.strip() or line.startswith('*'):
        continue
    parts = line.split()
    if len(parts) >= 5:
        date_str = parts[0]
        start_str = parts[1]
        peak_str = parts[2]
        end_str = parts[3]
        flare_class = parts[4]
        
        try:
            peak_dt = pd.to_datetime(f'{date_str} {peak_str}')
            events.append({'peak_dt': peak_dt, 'class': flare_class})
        except:
            pass

goes = pd.DataFrame(events)
june6 = pd.to_datetime('2026-06-06')
june16 = pd.to_datetime('2026-06-16')
june18 = pd.to_datetime('2026-06-18')

goes_0615 = goes[(goes['peak_dt'] >= june6) & (goes['peak_dt'] < june16)]
goes_1618 = goes[(goes['peak_dt'] >= june16) & (goes['peak_dt'] <= june18)]

print(f'GOES flares June 6-15 (before detection window): {len(goes_0615)}')
print(f'GOES flares June 16-18 (during/after detection): {len(goes_1618)}')
print(f'Total June 6-18: {len(goes_0615) + len(goes_1618)}')
print()
print('SoLEXS detected June 13-18: 92 events')
print(f'SoLEXS detection captured {92} / {len(goes_1618)} GOES flares (if any overlap)')

import argparse
import pandas as pd
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUTPUT_DIR = ROOT / 'output'

DEFAULT_GOES = DATA_DIR / 'goes_xray_2026.txt'
DEFAULT_RHESSI = DATA_DIR / 'rhessi_flare_list.txt'
DEFAULT_FERMI = DATA_DIR / 'fermi_gbm_flare_list.txt'
DEFAULT_SOLEXS = OUTPUT_DIR / 'solexs_combined.csv'
DEFAULT_MATCHED = OUTPUT_DIR / 'matched_flares.csv'
DEFAULT_LABELED = OUTPUT_DIR / 'labeled_solexs.csv'
DEFAULT_MIN_DURATION = 60  # seconds; filter out events shorter than this

MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}


def parse_goes_events(path: Path):
    events = []
    with path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('GOES') or line.startswith('Written') or line.startswith('Columns:'):
                continue
            parts = re.split(r'\s+', line)
            if len(parts) < 5:
                continue
            date_token, start, peak, end, flare_class = parts[:5]
            if not re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{4}$', date_token):
                continue
            try:
                day, mon, year = date_token.split('-')
                date_str = f"{year}{MONTH_MAP[mon]:02d}{int(day):02d}"
            except Exception:
                continue
            events.append({
                'DATE': date_str,
                'START': start,
                'PEAK': peak,
                'END': end,
                'CLASS': flare_class,
                'SOURCE': 'GOES',
            })
    return events


def parse_rhessi_events(path: Path):
    events = []
    with path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('HESSI Flare List') or line.startswith('Total # flares:') or line.startswith('Flare'):
                continue
            parts = re.split(r'\s+', line)
            if len(parts) >= 5 and re.match(r'^\d{7,8}$', parts[0]) and re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{4}$', parts[1]):
                start = parts[2]
                peak = parts[3]
                end = parts[4]
                try:
                    date_str = pd.to_datetime(f"{parts[1]} {start}", utc=True).strftime('%Y%m%d')
                except Exception:
                    date_str = None
                if date_str:
                    events.append({
                        'DATE': date_str,
                        'START': start,
                        'PEAK': peak,
                        'END': end,
                        'CLASS': 'RHESSI',
                        'SOURCE': 'RHESSI',
                    })
                    continue
            if len(parts) >= 4:
                generic = parse_generic_event_list_from_parts(parts, 'RHESSI')
                if generic:
                    events.extend(generic)
    return events


def parse_generic_event_list(path: Path, source: str):
    events = []
    with path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('!') or line.startswith('//'):
                continue
            parts = re.split(r'\s+', line)
            if len(parts) < 4:
                continue
            generic = parse_generic_event_list_from_parts(parts, source)
            if generic:
                events.extend(generic)
    return events


def parse_generic_event_list_from_parts(parts, source):
    date_token = parts[0]
    try:
        date_obj = pd.to_datetime(date_token, utc=True)
        date_str = date_obj.strftime('%Y%m%d')
    except Exception:
        return []
    start = parts[1]
    peak = parts[2]
    end = parts[3] if len(parts) >= 4 else parts[1]
    flare_class = source
    if len(parts) >= 5:
        flare_class = parts[4]
    return [{
        'DATE': date_str,
        'START': start,
        'PEAK': peak,
        'END': end,
        'CLASS': flare_class,
        'SOURCE': source,
    }]


def load_event_catalogs(goes_path: Path, rhessi_path: Path, fermi_path: Path):
    all_events = []

    if goes_path.exists():
        goes_events = parse_goes_events(goes_path)
        print(f'Loaded {len(goes_events)} GOES events from {goes_path.name}')
        all_events.extend(goes_events)
    else:
        print(f'GOES file not found: {goes_path} (skipping GOES labels)')

    if rhessi_path.exists():
        rhessi_events = parse_rhessi_events(rhessi_path)
        print(f'Loaded {len(rhessi_events)} RHESSI events from {rhessi_path.name}')
        all_events.extend(rhessi_events)
    else:
        print(f'RHESSI file not found: {rhessi_path} (skipping RHESSI labels)')

    if fermi_path.exists():
        fermi_events = parse_generic_event_list(fermi_path, 'FERMI_GBM')
        print(f'Loaded {len(fermi_events)} Fermi/GBM events from {fermi_path.name}')
        all_events.extend(fermi_events)
    else:
        print(f'Fermi/GBM file not found: {fermi_path} (skipping Fermi labels)')

    return pd.DataFrame(all_events)


def label_solexs(solexs_csv: Path, goes_path: Path, rhessi_path: Path, fermi_path: Path, output_matched: Path, output_labeled: Path, min_duration: int = DEFAULT_MIN_DURATION):
    solexs = pd.read_csv(solexs_csv)
    print(f'Loaded {len(solexs)} SoLEXS data points from {solexs_csv}')
    solexs['DATETIME'] = pd.to_datetime(solexs['TIME'], unit='s', origin='unix', utc=True)
    solexs['DATE'] = solexs['DATETIME'].dt.strftime('%Y%m%d')

    flares_df = load_event_catalogs(goes_path, rhessi_path, fermi_path)
    if flares_df.empty:
        print('No candidate X-ray events loaded; cannot label SoLEXS data.')
        return

    print(f'Total candidate X-ray events: {len(flares_df)}')
    solexs_dates = sorted(solexs['DATE'].unique())
    print(f'Your SoLEXS dates: {solexs_dates}')

    matching_flares = flares_df[flares_df['DATE'].isin(solexs_dates)].copy()
    print(f'\nTotal matching X-ray events: {len(matching_flares)}')

    if matching_flares.empty:
        print('No matching events found for your SoLEXS dates.')

    matching_flares['START_DT'] = pd.to_datetime(
        matching_flares['DATE'] + ' ' + matching_flares['START'], errors='coerce', utc=True
    )
    matching_flares['END_DT'] = pd.to_datetime(
        matching_flares['DATE'] + ' ' + matching_flares['END'], errors='coerce', utc=True
    )
    matching_flares['PEAK_DT'] = pd.to_datetime(
        matching_flares['DATE'] + ' ' + matching_flares['PEAK'], errors='coerce', utc=True
    )
    matching_flares = matching_flares.dropna(subset=['START_DT', 'END_DT'])

    # Filter out implausibly short events (likely noise / bad catalog entries)
    try:
        durations = (matching_flares['END_DT'] - matching_flares['START_DT']).dt.total_seconds()
        before_count = len(matching_flares)
        matching_flares = matching_flares[durations >= float(min_duration)].copy()
        after_count = len(matching_flares)
        if before_count != after_count:
            print(f'Filtered out {before_count - after_count} events shorter than {min_duration} seconds')
    except Exception:
        # if dt arithmetic fails, skip filtering but warn
        print('Warning: could not compute event durations for filtering')

    # Compute number of SoLEXS samples in each candidate event interval and filter by sample count
    try:
        sample_counts = []
        for _, flare in matching_flares.iterrows():
            s = flare['START_DT']
            e = flare['END_DT']
            cnt = int(((solexs['DATETIME'] >= s) & (solexs['DATETIME'] <= e)).sum())
            sample_counts.append(cnt)
        matching_flares['SAMPLES'] = sample_counts
        before_count = len(matching_flares)
        matching_flares = matching_flares[matching_flares['SAMPLES'] > 2].copy()
        after_count = len(matching_flares)
        if before_count != after_count:
            print(f'Filtered out {before_count - after_count} events with SAMPLES <= 2')
    except Exception:
        print('Warning: could not compute SAMPLES for events')

    solexs['IS_FLARE'] = False
    solexs['FLARE_CLASS'] = None
    solexs['FLARE_SOURCE'] = None
    solexs['FLARE_START'] = pd.Series(pd.NaT, index=solexs.index, dtype='datetime64[ns, UTC]')
    solexs['FLARE_END'] = pd.Series(pd.NaT, index=solexs.index, dtype='datetime64[ns, UTC]')
    solexs['LABEL_SOURCES'] = ''

    for _, flare in matching_flares.iterrows():
        start_dt = flare['START_DT']
        end_dt = flare['END_DT']
        mask = (solexs['DATETIME'] >= start_dt) & (solexs['DATETIME'] <= end_dt)
        if not mask.any():
            continue
        solexs.loc[mask, 'IS_FLARE'] = True
        if flare['SOURCE'] == 'GOES' or solexs.loc[mask, 'FLARE_CLASS'].isna().all():
            solexs.loc[mask, 'FLARE_CLASS'] = flare['CLASS']
        solexs.loc[mask, 'FLARE_SOURCE'] = flare['SOURCE']
        solexs.loc[mask, 'FLARE_START'] = start_dt
        solexs.loc[mask, 'FLARE_END'] = end_dt
        current_sources = solexs.loc[mask, 'LABEL_SOURCES']
        updated_sources = current_sources.apply(
            lambda x: ';'.join(sorted(set([s for s in x.split(';') if s] + [flare['SOURCE']]))) if x else flare['SOURCE']
        )
        solexs.loc[mask, 'LABEL_SOURCES'] = updated_sources

    flare_samples = int(solexs['IS_FLARE'].sum())
    print(f'\nLabeled {flare_samples} SoLEXS rows as flare samples')

    output_matched.parent.mkdir(parents=True, exist_ok=True)
    output_labeled.parent.mkdir(parents=True, exist_ok=True)
    matching_flares.to_csv(output_matched, index=False)
    solexs.to_csv(output_labeled, index=False)
    print(f'\nSaved {output_matched} and {output_labeled}')

    print('\nFlare source breakdown:')
    print(matching_flares['SOURCE'].value_counts())
    print('\nFlare samples by class in labeled SoLEXS data:')
    print(solexs[solexs['IS_FLARE']]['FLARE_CLASS'].value_counts())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Label SoLEXS rows with external X-ray event catalogs')
    parser.add_argument('--solexs-csv', default=str(DEFAULT_SOLEXS), help='Input SoLEXS combined CSV')
    parser.add_argument('--goes', default=str(DEFAULT_GOES), help='GOES X-ray event list file')
    parser.add_argument('--rhessi', default=str(DEFAULT_RHESSI), help='RHESSI flare event list file')
    parser.add_argument('--fermi', default=str(DEFAULT_FERMI), help='Fermi/GBM flare event list file')
    parser.add_argument('--output-matched', default=str(DEFAULT_MATCHED), help='Output matched flare catalog CSV')
    parser.add_argument('--output-labeled', default=str(DEFAULT_LABELED), help='Output labeled SoLEXS CSV')
    parser.add_argument('--min-duration', default=int(DEFAULT_MIN_DURATION), type=int, help='Minimum flare duration in seconds to accept (filters catalog events shorter than this)')
    args = parser.parse_args()
    label_solexs(
        Path(args.solexs_csv),
        Path(args.goes),
        Path(args.rhessi),
        Path(args.fermi),
        Path(args.output_matched),
        Path(args.output_labeled),
        min_duration=args.min_duration,
    )

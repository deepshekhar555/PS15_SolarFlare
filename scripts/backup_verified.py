import shutil
from pathlib import Path
orig_files = {
    'solexs_combined.csv': Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv'),
    'matched_flares.csv': Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/matched_flares.csv'),
    'labeled_solexs.csv': Path('D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/labeled_solexs.csv'),
    'goes_xray_2026.txt': Path('D:/PS15_SolarFlare/data/goes_xray_2026.txt'),
}
backup_dir = Path('D:/PS15_SolarFlare/backup_verified_20260619')
backup_dir.mkdir(parents=True, exist_ok=True)
results = []
for name, src in orig_files.items():
    dst = backup_dir / name
    try:
        if not src.exists():
            results.append((name, 'MISSING', None, None))
            continue
        shutil.copy2(src, dst)
        s_src = src.stat().st_size
        s_dst = dst.stat().st_size
        status = 'OK' if s_src == s_dst else 'SIZE_MISMATCH'
        results.append((name, status, s_src, s_dst))
    except Exception as e:
        results.append((name, 'ERROR', str(e), None))

print('BACKUP_DIR:', str(backup_dir))
print('RESULTS:')
for r in results:
    print(r)

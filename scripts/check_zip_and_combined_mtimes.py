import glob, os, datetime
from pathlib import Path

zip_pattern = r'D:\PS15_SolarFlare\data\solexs\AL1_SLX_L1_*.zip*'
zip_paths = sorted(glob.glob(zip_pattern))
print('FILE\tMTIME\tSIZE')
for p in zip_paths:
    try:
        st = os.stat(p)
        m = datetime.datetime.fromtimestamp(st.st_mtime)
        print(f"{os.path.basename(p)}\t{m.isoformat()}\t{st.st_size}")
    except Exception as e:
        print(f"{os.path.basename(p)}\tERROR\t{e}")

combined = Path(r'D:/PS15_SolarFlare/Solar Low Energy X-ray Spectrometer/output/solexs_combined.csv')
if combined.exists():
    st = combined.stat()
    m = datetime.datetime.fromtimestamp(st.st_mtime)
    print('\nCOMBINED_CSV\tMTIME\tSIZE')
    print(f"{combined.name}\t{m.isoformat()}\t{st.st_size}")
else:
    print('\nCOMBINED_CSV\tMISSING')

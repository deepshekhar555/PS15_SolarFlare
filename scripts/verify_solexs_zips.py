import glob, os
paths = glob.glob(r'D:\PS15_SolarFlare\data\solexs\AL1_SLX_L1_*.zip*')
paths = sorted(paths)
if not paths:
    print('No files found')
    raise SystemExit(0)
print('FILE\tSIZE\tHEX4\tTYPE')
for p in paths:
    try:
        size = os.path.getsize(p)
        with open(p, 'rb') as f:
            head = f.read(64)
        hex4 = head[:4].hex()
        head_lower = head.lower()
        starts_html = head_lower.startswith(b'<!do') or head_lower.startswith(b'<html')
        is_zip = head.startswith(b'PK\x03\x04')
        typ = 'ZIP' if is_zip else ('HTML' if starts_html else 'OTHER')
        print(f"{os.path.basename(p)}\t{size}\t{hex4}\t{typ}")
    except Exception as e:
        print(f"{os.path.basename(p)}\tERROR\t{e}")

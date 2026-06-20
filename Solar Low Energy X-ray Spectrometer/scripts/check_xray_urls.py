import urllib.request
import urllib.error

urls = [
    'http://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.txt',
    'http://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.dat',
    'https://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.txt',
    'https://hesperia.gsfc.nasa.gov/hessidata/dbase/hessi_flare_list.dat',
    'https://heasarc.gsfc.nasa.gov/FTP/rhessi/hessi_flare_list.txt',
    'https://fermi.gsfc.nasa.gov/ssc/data/access/gbm/solar/flare_list.txt',
    'https://gammaray.msfc.nasa.gov/gbm/trigger_history.txt',
]

for u in urls:
    try:
        print('TRY', u)
        with urllib.request.urlopen(u, timeout=20) as r:
            data = r.read(500)
            print('OK', len(data), repr(data[:200]))
    except urllib.error.HTTPError as e:
        print('HTTP ERROR', u, e.code, e.reason)
    except urllib.error.URLError as e:
        print('URL ERROR', u, e.reason)
    except Exception as e:
        print('ERROR', u, type(e).__name__, e)

import urllib.request

url = 'http://127.0.0.1:8000/'
try:
    r = urllib.request.urlopen(url, timeout=10)
    print('STATUS', r.getcode())
    data = r.read(16000)
    print(data.decode('utf-8', errors='replace'))
except Exception as e:
    print('ERROR', e)

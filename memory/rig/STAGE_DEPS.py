"""Download locked pure-Python wheels and audit metadata; execute no package code."""
import datetime, hashlib, json, pathlib, urllib.request, zipfile, io, tarfile
HERE = pathlib.Path(__file__).resolve().parent
DEST = HERE / 'staged/dependencies'
PINS = {'h2':'4.4.1','hpack':'4.2.0','hyperframe':'6.1.0','html5lib':'1.1',
        'six':'1.17.0','webencodings':'0.5.1','pywebsocket3':'4.0.2','atomicwrites':'1.4.1'}
def get(url):
    with urllib.request.urlopen(url, timeout=60) as r: return r.read()
def main():
    DEST.mkdir(parents=True, exist_ok=True); locked=[]
    for name, version in PINS.items():
        meta=json.loads(get(f'https://pypi.org/pypi/{name}/{version}/json'))
        (DEST/(name+'-metadata.json')).write_text(json.dumps(meta, indent=2))
        wheels=[x for x in meta['urls'] if x['filename'].endswith('none-any.whl')]
        w=wheels[0] if wheels else next(x for x in meta['urls'] if x['packagetype']=='sdist')
        raw=get(w['url']); sha=hashlib.sha256(raw).hexdigest()
        assert sha==w['digests']['sha256']
        (DEST/w['filename']).write_bytes(raw)
        if wheels:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                hooks=[p for p in z.namelist() if p.endswith(('.pth','.so','.dll')) or '/scripts/' in p]
                source={p:z.read(p).decode('utf-8',errors='replace') for p in z.namelist() if p.endswith('.py')}
        else:
            with tarfile.open(fileobj=io.BytesIO(raw)) as t:
                source={p.name:t.extractfile(p).read().decode('utf-8',errors='replace') for p in t if p.isfile() and p.name.endswith('.py')}
            hooks=['sdist setup.py present; never executed; copy package sources only']
        (DEST/(name+'-source.json')).write_text(json.dumps(source,indent=2))
        age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(w['upload_time_iso_8601'].replace('Z','+00:00'))).days
        locked.append(dict(name=name,version=version,file=w['filename'],url=w['url'],sha256=sha,
            uploaded=w['upload_time_iso_8601'],age_days=age,under_seven_days=age<7,
            requires_dist=meta['info'].get('requires_dist'),install_hook_flags=hooks))
    req=urllib.request.Request('https://api.osv.dev/v1/querybatch',
        data=json.dumps({'queries':[{'package':{'name':x['name'],'ecosystem':'PyPI'},'version':x['version']} for x in locked]}).encode(),
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r: osv=json.load(r)
    (DEST/'OSV.json').write_text(json.dumps(osv,indent=2))
    (HERE/'DEPENDENCIES.lock.json').write_text(json.dumps(dict(packages=locked,osv=osv),indent=2)+'\n')
    (HERE/'requirements.lock').write_text(''.join(x['name']+'=='+x['version']+' --hash=sha256:'+x['sha256']+'\n' for x in locked))
    print(json.dumps({'count':len(locked),'young':[x['name'] for x in locked if x['under_seven_days']],
        'hooks':[x['name'] for x in locked if x['install_hook_flags']], 'osv':osv}))
if __name__=='__main__': main()

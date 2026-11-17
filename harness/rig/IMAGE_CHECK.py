"""Check offline image contents before building services or starting any engine."""
import argparse, hashlib, json, os, pathlib, stat

NAMES = {'agent-browser', 'lightpanda', 'obscura', 'obscura-worker', 'moli'}

def executable(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('missing/non-regular executable: '+str(path))
    if not stat.S_IMODE(path.stat().st_mode) & 0o111 or not os.access(path, os.X_OK):
        raise ValueError('not executable: '+str(path))
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def check(root, manifest, installed_root=pathlib.Path('/opt/headless')):
    hashes=manifest['binary_sha256']
    if set(hashes)!=NAMES:
        raise ValueError('binary manifest names differ')
    receipt={}
    for name, expected in hashes.items():
        actual=executable(root/'bin'/name)
        if actual!=expected:
            raise ValueError('binary SHA256 mismatch: '+name)
        receipt[name]=dict(sha256=actual,state='verified')
    configured=pathlib.Path((root/'CHROME_PATH.txt').read_text().strip())
    relative=configured.relative_to(installed_root)
    if '..' in relative.parts or configured.name!='chrome':
        raise ValueError('unsafe Chrome executable path')
    chrome_sha=executable(root/relative)
    receipt['chrome']=dict(sha256=chrome_sha,state='present-in-pinned-chrome-image',
        image=manifest['chrome_image'],note='Binary hash recorded; image ID and prior archive receipt bind publisher provenance.')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--manifest',required=True);a=p.parse_args()
    print(json.dumps(check(pathlib.Path(a.root),json.loads(pathlib.Path(a.manifest).read_text())),indent=2))

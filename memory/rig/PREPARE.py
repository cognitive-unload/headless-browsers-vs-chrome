"""Offline preparation of reviewed source/data. No downloaded code runs."""
import argparse, hashlib, io, json, os, pathlib, shutil, subprocess, tarfile, zipfile
from TLS_COMPAT import patch as patch_websocket_tls

KIT=pathlib.Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(root,name):
    p=pathlib.PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe archive path')
    return root.joinpath(*p.parts)
def unpack_source(archive,root,prefix=None,skip=()):
    with tarfile.open(archive) as t:
        for m in t:
            name=m.name.partition('/')[2]
            if prefix:
                if not name.startswith(prefix):continue
                name=name[len(prefix):]
            if not name or any(name.startswith(x) for x in skip):continue
            if m.isdir():continue
            if not m.isfile():
                # Reject links rather than allowing a build context to escape its root.
                raise ValueError('non-regular source archive member '+m.name)
            dest=safe(root,name);dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(t.extractfile(m).read());dest.chmod(0o644)

def main():
    # Host-name gate removed for publication (see SANITISATION.md).
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--deps',required=True)
    parser.add_argument('--output',required=True);a=parser.parse_args()
    output=pathlib.Path(a.output)
    output.mkdir(parents=True,exist_ok=False)
    source=pathlib.Path(a.source);deps=pathlib.Path(a.deps)
    sample=json.loads((KIT/'WPT_SAMPLE.json').read_text())
    if digest(source/'WPT.tar.gz')!=sample['archive_sha256']:raise ValueError('WPT archive SHA256 mismatch')
    if digest(source/'DEMO.tar.gz')!='700157c2941dbb7e120c9ded6c0aff7179ada83b4353b1260c04a6eb21dc702c':raise ValueError('demo SHA256 mismatch')
    wpt=output/'wpt';wpt.mkdir();unpack_source(source/'WPT.tar.gz',wpt,skip=('tools/third_party/',))
    for test in sample['tests']:
        if digest(wpt/test['source'])!=test['sha256']:raise ValueError('selected test SHA mismatch')
    rig=output/'rig';shutil.copytree(KIT,rig,ignore=shutil.ignore_patterns('REVIEW_BUNDLE.md','REVIEW_CLEARANCE.json','staged','__pycache__','*.pyc'))
    original=wpt/'resources/testharness.js'
    original_sha=digest(original)
    original.write_bytes(original.read_bytes()+b'\n'+(KIT/'COLLECTOR.js').read_bytes())
    fixture=wpt/'__rig';fixture.mkdir()
    (fixture/'known.html').write_text('<!doctype html><script src="/resources/testharness.js"></script><script>test(()=>assert_true(true),"known pass");test(()=>assert_true(false),"known fail");</script>')
    (fixture/'motion.html').write_text('<!doctype html><style>#box{width:50px;height:50px;background:red;transform:translateX(0);transition:transform 1s linear}</style><button id="move">Move</button><div id="box"></div><script>window.motionDone=false;move.onclick=()=>{box.addEventListener("transitionend",()=>window.motionDone=true,{once:true});box.style.transform="translateX(500px)"}</script>')
    for color in ('red','blue'):
        (fixture/(color+'.html')).write_text('<!doctype html><html class="reftest-wait"><style>div{width:100px;height:100px;background:'+color+'}</style><div></div><script>document.documentElement.addEventListener("TestRendered",()=>document.documentElement.classList.remove("reftest-wait"),{once:true})</script>')
    public=output/'demo';public.mkdir();unpack_source(source/'DEMO.tar.gz',public,prefix='public/campfire-commerce/')
    # The server directory layout preserves the original benchmark URL.
    demo_parent=output/'demo-root';demo_parent.mkdir();shutil.move(public,demo_parent/'campfire-commerce')
    python=rig/'python';python.mkdir()
    lock=json.loads((KIT/'DEPENDENCIES.lock.json').read_text())
    for package in lock['packages']:
        asset=deps/package['file']
        if digest(asset)!=package['sha256']:raise ValueError('dependency SHA mismatch '+package['name'])
        if asset.suffix=='.whl':
            with zipfile.ZipFile(asset) as z:
                for name in z.namelist():
                    if name.endswith('/') or name=='webencodings/mklabels.py':continue
                    dest=safe(python,name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
        else:
            if package['name'] not in ('pywebsocket3','atomicwrites'):raise ValueError('unreviewed source package')
            unpack_source(asset,python/package['name'],prefix=package['name']+'/')
    tls_repair=patch_websocket_tls(python/'pywebsocket3/websocket_server.py')
    # Only public WPT fixture certificate material, never a personal key.
    cert=wpt/'tools/certs/web-platform.test.pem'
    key=subprocess.run(['openssl','x509','-in',str(cert),'-pubkey','-noout'],capture_output=True,check=True).stdout
    der=subprocess.run(['openssl','pkey','-pubin','-outform','DER'],input=key,capture_output=True,check=True).stdout
    import base64
    (rig/'WPT_SPKI.txt').write_text(base64.b64encode(hashlib.sha256(der).digest()).decode()+'\n')
    shutil.copyfile(KIT/'Dockerfile',output/'Dockerfile')
    (output/'PREPARE_RECEIPT.json').write_text(json.dumps(dict(wpt=sample['commit'],archive_sha256=sample['archive_sha256'],
        collector_original_sha256=original_sha,collector_modified_sha256=digest(original),packages=lock['packages'],tls_repair=tls_repair),indent=2))
    print(str(output))
if __name__=='__main__':main()

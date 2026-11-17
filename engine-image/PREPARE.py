"""On the test host, within a job scratch directory: download and verify release files; never run them."""
import hashlib,json,os,pathlib,shutil,tarfile,urllib.request,zipfile

kit=pathlib.Path(__file__).resolve().parent
scratch=pathlib.Path(os.environ['HEAVY_JOB_SCRATCH_DIR'])/'headless-smoke-20261109-r1'
scratch.mkdir(parents=True,exist_ok=True)
context=scratch/'context';context.mkdir(exist_ok=True)
runtime=context/'runtime';runtime.mkdir(exist_ok=True)
(runtime/'bin').mkdir(exist_ok=True)
receipts=[]

def target_path(root,name):
    path=pathlib.PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:raise ValueError('unsafe archive member: '+name)
    return root.joinpath(*path.parts)

for asset in json.loads((kit/'ARTIFACTS.json').read_text())['assets']:
    digest=asset['sha256']
    if not digest:
        receipts.append(dict(name=asset['name'],state='held',reason=asset['hold']))
        continue
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('invalid pinned SHA256')
    archive=scratch/asset['name']
    if not archive.exists():
        request=urllib.request.Request(asset['url'],headers={'User-Agent':'headless-smoke'})
        with urllib.request.urlopen(request,timeout=120) as response,archive.open('wb') as output:
            shutil.copyfileobj(response,output)
    hasher=hashlib.sha256()
    with archive.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):hasher.update(chunk)
    actual=hasher.hexdigest()
    if actual!=digest:raise ValueError('SHA256 mismatch: '+asset['name'])
    dest=runtime/asset['name'].split('.')[0];dest.mkdir(exist_ok=True)
    if asset['kind']=='binary':
        name='agent-browser' if asset['name'].startswith('agent-browser') else 'lightpanda'
        shutil.copyfile(archive,runtime/'bin'/name);(runtime/'bin'/name).chmod(0o755)
    elif asset['kind']=='tar':
        with tarfile.open(archive,'r:gz') as source:
            for member in source.getmembers():
                path=target_path(dest,member.name)
                if member.isdir():path.mkdir(parents=True,exist_ok=True);continue
                if not member.isfile():raise ValueError('non-regular archive member: '+member.name)
                if member.size>1024*1024*1024:raise ValueError('archive member too large')
                path.parent.mkdir(parents=True,exist_ok=True)
                with source.extractfile(member) as incoming,path.open('wb') as output:shutil.copyfileobj(incoming,output)
                path.chmod(0o755 if member.mode&0o111 else 0o644)
        for name in (['obscura','obscura-worker'] if asset['name'].startswith('obscura') else ['moli']):
            choices=[p for p in dest.rglob(name) if p.is_file()]
            if len(choices)!=1:raise ValueError('ambiguous/missing binary: '+name)
            shutil.copyfile(choices[0],runtime/'bin'/name);(runtime/'bin'/name).chmod(0o755)
    elif asset['kind']=='zip':
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                path=target_path(dest,member.filename)
                mode=member.external_attr>>16
                if mode&0o170000==0o120000:raise ValueError('zip symlink rejected')
                if member.is_dir():path.mkdir(parents=True,exist_ok=True);continue
                path.parent.mkdir(parents=True,exist_ok=True)
                with source.open(member) as incoming,path.open('wb') as output:shutil.copyfileobj(incoming,output)
                path.chmod(0o755 if mode&0o111 else 0o644)
        candidates=list(dest.rglob('chrome'))
        if len(candidates)!=1:raise ValueError('ambiguous/missing chrome')
        (runtime/'CHROME_PATH.txt').write_text('/opt/headless/'+str(candidates[0].relative_to(runtime)))
    receipts.append(dict(name=asset['name'],version=asset['version'],url=asset['url'],expected_sha256=digest,actual_sha256=actual,size=archive.stat().st_size,state='verified'))
    print('verified',asset['name'],actual,flush=True)

for name in ['Dockerfile','SMOKE.py','.dockerignore']:shutil.copyfile(kit/name,context/name)
(runtime/'ARTIFACT_RECEIPTS.json').write_text(json.dumps(receipts,indent=2))
(scratch/'ARTIFACT_RECEIPTS.json').write_text(json.dumps(receipts,indent=2))
(kit/'LAST_SCRATCH.txt').write_text(str(scratch)+'\n')
print('context',str(context),flush=True)

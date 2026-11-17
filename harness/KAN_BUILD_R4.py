"""Bounded offline Kan build in containers; see README.md."""
import hashlib,json,os,pathlib,subprocess,sys,tarfile
ROOT=pathlib.Path(os.environ['KAN_ROOT'])
NODE='sha256:07da4b3bda51fd1973b20d19d7139b289e0e065e364990bb26a80bb1e46cf757'
attempt=sys.argv[1] if len(sys.argv)>1 else 'R4'
assert attempt in ['R1','R2','R3','R4']
# Host-name gate removed for publication (see SANITISATION.md).
work=ROOT/('build-'+attempt);work.mkdir()
source=work/'source';source.mkdir();store=ROOT/'pnpm-store';store.mkdir(exist_ok=True)
tools=ROOT/'pnpm';tools.mkdir(exist_ok=True)
receipt={'attempt':attempt,'node_image':NODE,'steps':[]}
def extract(archive,destination):
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            p=pathlib.PurePosixPath(m.name)
            if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe archive member')
            if m.issym() or m.islnk():
                q=pathlib.PurePosixPath(m.linkname)
                if q.is_absolute() or '..' in q.parts:raise ValueError('unsafe archive link')
        t.extractall(destination)
assert hashlib.sha256((ROOT/'PNPM.tgz').read_bytes()).hexdigest()=='06e65a4965baff6d6097f9c8f75c35f6d420974dbc03d775009056a69edfd271'
extract(ROOT/'KAN_SOURCE.tar',source)
if not (tools/'package/bin/pnpm.cjs').exists():extract(ROOT/'PNPM.tgz',tools)
manifest=json.loads((ROOT/'SOURCE_SHA256.json').read_text())
assert all(hashlib.sha256((source/f).read_bytes()).hexdigest()==h for f,h in manifest.items())
config_file=source/'apps/web/next.config.js'
build_setting='\n// Capture build: mirror upstream Turbopack SVG rule in webpack.\nconfig.webpack = (c) => { const imageRule=c.module.rules.find(r=>r.test?.test?.(".svg")); if(imageRule) imageRule.exclude=/\\.svg$/i; c.module.rules.push({test:/\\.svg$/i,use:["@svgr/webpack"]}); return c; };\n'
original=config_file.read_text();config_file.write_text(original.replace('export default config;',build_setting+'\nexport default config;'))
(work/'BUILD_SETTINGS_DIFF.txt').write_text(build_setting)
for folder in [work,store]:subprocess.run(['chown','-R','1000:1000',str(folder)],check=True)
env={'PATH':'/work/node_modules/.bin:/usr/local/bin:/usr/bin:/bin','HOME':'/tmp/home','XDG_CACHE_HOME':'/tmp/cache','CI':'true','NEXT_TELEMETRY_DISABLED':'1','TURBO_TELEMETRY_DISABLED':'1','npm_config_ignore_scripts':'true','npm_config_registry':'https://registry.npmjs.org/','npm_config_update_notifier':'false','COREPACK_ENABLE_PROJECT_SPEC':'0','NEXT_FONT_GOOGLE_MOCKED_RESPONSES':'/opt/kan-build/fonts/mock.cjs','NEXT_PUBLIC_USE_STANDALONE_OUTPUT':'true','NEXT_PUBLIC_BASE_URL':'http://127.0.0.1:3000','BETTER_AUTH_SECRET':os.environ['KAN_AUTH_SECRET'],'POSTGRES_URL':'postgresql://capture:'+os.environ['KAN_DB_PASSWORD']+'@127.0.0.1:5432/kan_capture','NEXT_PUBLIC_ALLOW_CREDENTIALS':'true','NEXT_PUBLIC_DISABLE_EMAIL':'true','AWS_EC2_METADATA_DISABLED':'true'}
common=['docker','run','--read-only','--user','1000:1000','--cap-drop=ALL','--security-opt','no-new-privileges','--pids-limit','1024','--cpus','2','--memory','8g','--tmpfs','/tmp:rw,nosuid,nodev,size=1g,uid=1000,gid=1000','--mount',f'type=bind,source={source},target=/work','--mount',f'type=bind,source={store},target=/store','--mount',f'type=bind,source={tools}/package,target=/opt/pnpm,readonly','--mount',f'type=bind,source={ROOT}/font-input,target=/opt/kan-build/fonts,readonly','--workdir','/work','--entrypoint','/usr/local/bin/node']
for k,v in env.items():common+=['--env',k+'='+v]
entry=ROOT/'BUILD_ENTRY.cjs'
entry.write_text("const c=require('node:child_process');const run=(args,cwd='/work')=>{let r=c.spawnSync('/usr/local/bin/node',['/opt/pnpm/bin/pnpm.cjs',...args],{cwd,env:process.env,stdio:'inherit'});if(r.status!==0)process.exit(r.status??1)};run(['install','--offline','--frozen-lockfile','--ignore-scripts','--store-dir','/store']);let m=c.spawnSync('/usr/local/bin/node',['/work/node_modules/typescript/bin/tsc','--noEmit','false','--declaration','false','--emitDeclarationOnly','false','--outDir','dist'],{cwd:'/work/packages/mcp',env:process.env,stdio:'inherit'});if(m.status!==0)process.exit(m.status??1);let n=c.spawnSync('/usr/local/bin/node',['/work/node_modules/next/dist/bin/next','build','--no-lint'],{cwd:'/work/apps/web',env:process.env,stdio:'inherit'});process.exit(n.status??1);\n")
common+=['--mount',f'type=bind,source={entry},target=/opt/BUILD_ENTRY.cjs,readonly']
def run(label,network,args):
    name='kan-'+label+'-'+attempt.lower()
    cmd=common+['--name',name,'--label','rig.fixture=1','--network',network,NODE]+args
    with (work/(label+'.log')).open('w') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    inspection=json.loads(subprocess.check_output(['docker','inspect',name]))
    receipt['steps'].append({'label':label,'exit_code':result.returncode,'container':inspection,'log':str(work/(label+'.log'))})
    (work/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(label,'exit',result.returncode,flush=True)
    if result.returncode:raise RuntimeError(label+' failed; preserve this attempt and inspect its log')
run('registry-fetch','bridge',['/opt/pnpm/bin/pnpm.cjs','fetch','--frozen-lockfile','--ignore-scripts','--store-dir','/store'])
run('offline-build','none',['/opt/BUILD_ENTRY.cjs'])
for f,h in manifest.items():
    if f=='apps/web/next.config.js':continue
    if hashlib.sha256((source/f).read_bytes()).hexdigest()!=h:raise RuntimeError('tracked source changed: '+f)
receipt['source_preserved']=True
receipt['allowed_build_settings_change']='apps/web/next.config.js: webpack SVG rule equivalent to upstream Turbopack rule'
receipt['standalone_server']=str(source/'apps/web/.next/standalone/apps/web/server.js')
receipt['build_succeeded']=pathlib.Path(receipt['standalone_server']).exists()
(work/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert receipt['build_succeeded']
print('KAN_BUILD_COMPLETE',attempt,flush=True)

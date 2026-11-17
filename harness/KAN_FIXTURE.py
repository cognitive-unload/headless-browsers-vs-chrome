"""Offline fixture controller; no Kan source mutations."""
import json, os, pathlib, shutil, subprocess, sys, time
ROOT=pathlib.Path(os.environ['KAN_ROOT'])
NODE='sha256:07da4b3bda51fd1973b20d19d7139b289e0e065e364990bb26a80bb1e46cf757'
PG='sha256:7296f210ae81031ec955dbad9a67a84fe958572a2153b8d0826a647522904dc1'
BROWSER='sha256:d97a2c45d5d3a2e5ef3bedf8bee68fd53d018b62d152f0c67a51ac5e2046dc08'
# Host-name gate removed for publication (see SANITISATION.md).
action,label=sys.argv[1:3]
assert label in ['setup','chrome','obscura','moli','lightpanda']
folder=ROOT/('fixture-'+label)
prefix='kan-fixture-'+label
names={k:prefix+'-'+k for k in ['browser','pg','web']}
URL='postgresql://capture:'+os.environ['KAN_DB_PASSWORD']+'@127.0.0.1:5432/kan_capture'
ENV={'HOME':'/tmp/home','NEXT_TELEMETRY_DISABLED':'1','TURBO_TELEMETRY_DISABLED':'1','NEXT_PUBLIC_BASE_URL':'http://127.0.0.1:3000','BETTER_AUTH_SECRET':os.environ['KAN_AUTH_SECRET'],'POSTGRES_URL':URL,'NEXT_PUBLIC_ALLOW_CREDENTIALS':'true','NEXT_PUBLIC_DISABLE_EMAIL':'true','AWS_EC2_METADATA_DISABLED':'true','HOSTNAME':'127.0.0.1','PORT':'3000'}
def run(args,**kw):
    return subprocess.run(args,check=True,**kw)
def output(args):return subprocess.check_output(args)
def inspect():
    data=json.loads(output(['docker','inspect',*names.values()]))
    (folder/'CONTAINERS.json').write_text(json.dumps(data,indent=2))
    for c in data:
        h=c['HostConfig'];assert not h['Privileged'] and h['ReadonlyRootfs'] and h['CapDrop']==['ALL']
        assert not h.get('PortBindings') and c['Config']['User'] in ['1000:1000','999:999']
        assert h['NetworkMode'] in ['none','container:'+json.loads(output(['docker','inspect',names['browser']]))[0]['Id']]
    return data
def sql(query):
    return output(['docker','exec',names['pg'],'psql','-U','capture','-d','kan_capture','-At','-c',query])
def observe():
    q='SELECT json_build_object(\'users\',(SELECT json_agg(t) FROM (SELECT id,name,email FROM "user")t),\'workspaces\',(SELECT json_agg(t) FROM (SELECT id,name FROM workspace WHERE "deletedAt" IS NULL)t),\'boards\',(SELECT json_agg(t) FROM (SELECT id,"publicId",name FROM board WHERE "deletedAt" IS NULL)t),\'lists\',(SELECT json_agg(t) FROM (SELECT id,name,"boardId","index" FROM list WHERE "deletedAt" IS NULL ORDER BY id)t),\'cards\',(SELECT json_agg(t) FROM (SELECT id,title,description,"listId","index" FROM card WHERE "deletedAt" IS NULL ORDER BY id)t));'
    return json.loads(sql(q))
if action=='up':
    folder.mkdir();(folder/'out').mkdir();(folder/'out').chmod(0o777)
    build=json.loads((ROOT/'build-R4/BUILD_RECEIPT.json').read_text())
    assert build.get('build_succeeded') and build.get('source_preserved')
    source=ROOT/'build-R4/source';standalone=source/'apps/web/.next/standalone'
    app=standalone/'apps/web'
    # Package static output alongside the traced production server, as Next requires.
    for src,dst in [(source/'apps/web/public',app/'public'),(source/'apps/web/.next/static',app/'.next/static')]:
        if not dst.exists():shutil.copytree(src,dst)
    common=['docker','run','-d','--read-only','--cap-drop=ALL','--security-opt','no-new-privileges','--label','rig.fixture=1']
    b=common+['--name',names['browser'],'--network','none','--user','1000:1000','--pids-limit','1024','--cpus','1.25','--memory','2560m','--shm-size','512m','--tmpfs','/tmp:rw,nosuid,nodev,size=1g,uid=1000,gid=1000','--tmpfs','/home/pwuser:rw,nosuid,nodev,size=256m,uid=1000,gid=1000','--add-host','telemetry.lightpanda.io:127.0.0.1','--env','LIGHTPANDA_DISABLE_TELEMETRY=1','--env','AGENT_BROWSER_NO_VERSION_CHECK=1','--env','KAN_TEST_PASSWORD','--mount',f'type=bind,source={folder}/out,target=/out','--mount',f'type=bind,source={ROOT}/kit,target=/opt/kan-capture,readonly','--entrypoint','/bin/sleep',BROWSER,'infinity']
    run(b,stdout=subprocess.DEVNULL)
    net='container:'+names['browser']
    p=common+['--name',names['pg'],'--network',net,'--user','999:999','--pids-limit','128','--cpus','.25','--memory','512m','--tmpfs','/tmp:rw,nosuid,nodev,size=128m,uid=999,gid=999','--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m,uid=999,gid=999','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=16m,uid=999,gid=999','--env','HOME=/tmp','--env','POSTGRES_USER=capture','--env','POSTGRES_PASSWORD='+os.environ['KAN_DB_PASSWORD'],'--env','POSTGRES_DB=kan_capture',PG,'postgres','-c','listen_addresses=127.0.0.1','-c','shared_buffers=64MB','-c','max_connections=30']
    run(p,stdout=subprocess.DEVNULL)
    # pg_isready alone can accept during the entrypoint's temporary init server.
    for _ in range(150):
        r=subprocess.run(['docker','logs',names['pg']],capture_output=True)
        if b'PostgreSQL init process complete; ready for start up.' in r.stdout+r.stderr:break
        time.sleep(.2)
    else:raise RuntimeError('Postgres initialization handoff deadline')
    for _ in range(100):
        r=subprocess.run(['docker','exec',names['pg'],'pg_isready','-U','capture','-d','kan_capture'],capture_output=True)
        if r.returncode==0:break
        time.sleep(.2)
    else:raise RuntimeError('Postgres readiness deadline')
    if label=='setup':
        cmd=['docker','run','--rm','--network',net,'--read-only','--user','1000:1000','--cap-drop=ALL','--security-opt','no-new-privileges','--cpus','.5','--memory','1g','--tmpfs','/tmp:rw,nosuid,nodev,size=128m,uid=1000,gid=1000','--env','HOME=/tmp','--env','POSTGRES_URL='+URL,'--mount',f'type=bind,source={source},target=/work,readonly','--workdir','/work/packages/db','--entrypoint','/usr/local/bin/node',NODE,'/work/node_modules/drizzle-kit/bin.cjs','migrate']
        with (folder/'MIGRATE.log').open('w') as log:run(cmd,stdout=log,stderr=subprocess.STDOUT)
    else:
        with (ROOT/'BASELINE.sql').open('rb') as seed:run(['docker','exec','-i',names['pg'],'psql','-v','ON_ERROR_STOP=1','-U','capture','-d','kan_capture'],stdin=seed,stdout=subprocess.DEVNULL)
    w=common+['--name',names['web'],'--network',net,'--user','1000:1000','--pids-limit','256','--cpus','.5','--memory','1g','--tmpfs','/tmp:rw,nosuid,nodev,size=128m,uid=1000,gid=1000','--mount',f'type=bind,source={standalone},target=/app,readonly','--workdir','/app/apps/web','--entrypoint','/usr/local/bin/node']
    for k,v in ENV.items():w+=['--env',k+'='+v]
    run(w+[NODE,'server.js'],stdout=subprocess.DEVNULL)
    inspect()
    for _ in range(150):
        r=subprocess.run(['docker','exec',names['browser'],'python3','-c',"import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:3000/login',timeout=2); assert r.status==200"],capture_output=True)
        if r.returncode==0:break
        time.sleep(.2)
    else:raise RuntimeError('Kan login health deadline: '+r.stderr.decode())
    (folder/'INITIAL_STATE.json').write_text(json.dumps(observe(),indent=2))
    print(json.dumps({'ready':True,'label':label,'containers':names}))
elif action=='observe':print(json.dumps(observe()))
elif action=='baseline':
    assert label=='setup'
    state=observe();assert len(state['users'])==1 and len(state['workspaces'])==1
    assert not state['boards'] and not state['lists'] and not state['cards']
    (ROOT/'BASELINE_STATE.json').write_text(json.dumps(state,indent=2))
    with (ROOT/'BASELINE.sql').open('wb') as f:run(['docker','exec',names['pg'],'pg_dump','-U','capture','-d','kan_capture','--no-owner','--no-privileges'],stdout=f)
    print('Synthetic user and empty workspace baseline saved')
elif action=='down':
    for k in ['web','pg','browser']:
        run(['docker','stop','--time','10',names[k]],stdout=subprocess.DEVNULL)
    inspect()
else:raise ValueError('Unknown fixture action')

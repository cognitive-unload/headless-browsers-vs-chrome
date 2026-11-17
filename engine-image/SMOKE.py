"""Deterministic public-page smoke test. No agent model, logins or uploads."""
import hashlib,json,os,pathlib,socket,subprocess,time,urllib.request

out=pathlib.Path('/out');out.mkdir(exist_ok=True)
root=pathlib.Path('/opt/headless')
base_env={'PATH':'/opt/headless/bin:/usr/local/bin:/usr/bin:/bin','HOME':'/home/pwuser','TMPDIR':'/tmp','LANG':'C.UTF-8','LIGHTPANDA_DISABLE_TELEMETRY':'1','AGENT_BROWSER_NO_VERSION_CHECK':'1'}
results=[]

def command(argv,env,timeout=65):
    started=time.monotonic()
    try:
        run=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=timeout)
        return dict(argv=argv,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,seconds=round(time.monotonic()-started,3))
    except subprocess.TimeoutExpired as error:
        def as_text(value):return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
        return dict(argv=argv,exit_code=None,error='process timeout',stdout=as_text(error.stdout),stderr=as_text(error.stderr),seconds=round(time.monotonic()-started,3))

blocked={item[4][0] for item in socket.getaddrinfo('telemetry.lightpanda.io',443)}
if not blocked or not blocked.issubset({'127.0.0.1','0.0.0.0','::1'}):raise RuntimeError('telemetry hostname is not blocked')
(out/'ISOLATION.json').write_text(json.dumps({'uid':os.getuid(),'telemetry_addresses':sorted(blocked),'environment_names':sorted(base_env),'personal_mounts':False,'published_ports':False},indent=2))

pages=[('example','https://example.com'),('wikipedia','https://en.wikipedia.org/wiki/Web_browser'),('github','https://github.com')]
for engine in ['chrome','lightpanda','obscura','moli']:
    env=dict(base_env);env['AGENT_BROWSER_SESSION']=engine
    argv=['/opt/headless/bin/agent-browser','--session',engine,'--json']
    moli=None;log=None
    if engine=='chrome':
        pin=root/'CHROME_PATH.txt'
        if pin.exists():argv+=['--executable-path',pin.read_text().strip()]
        else:
            for name,url in pages:results.append({'engine':engine,'page':name,'url':url,'state':'held','reason':'published Chrome SHA256 not resolved; Chrome not downloaded'})
            continue
    elif engine=='moli':
        log=(out/'moli-server.log').open('w')
        moli=subprocess.Popen(['/opt/headless/bin/moli','serve','--host','127.0.0.1','--port','9222','--layout','--resource'],env=env,stdout=log,stderr=log)
        argv+=['--cdp','http://127.0.0.1:9222']
        ready=False
        for attempt in range(100):
            if moli.poll() is not None:break
            try:
                with urllib.request.urlopen('http://127.0.0.1:9222/json/version',timeout=0.2) as response:json.load(response)
                ready=True;break
            except Exception:time.sleep(0.1)
        if not ready:
            for name,url in pages:results.append({'engine':engine,'page':name,'url':url,'state':'failed','reason':'Moli CDP not ready; see moli-server.log'})
            if moli.poll() is None:moli.terminate();moli.wait(timeout=10)
            log.close();continue
    else:argv+=['--engine',engine,'--executable-path','/opt/headless/bin/'+engine]
    try:
        (out/(engine+'-version.json')).write_text(json.dumps(command(['/opt/headless/bin/'+('agent-browser' if engine=='chrome' else engine),'--version'],env),indent=2))
        for name,url in pages:
            item={'engine':engine,'page':name,'url':url}
            item['open']=command(argv+['open',url],env)
            screenshot=out/(engine+'-'+name+'.png')
            # Screenshot is attempted after failed navigation too; errors are retained.
            item['screenshot']=command(argv+['screenshot',str(screenshot)],env)
            if screenshot.exists():
                data=screenshot.read_bytes();item['artifact']={'path':screenshot.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'png_signature':data[:8]==b'\x89PNG\r\n\x1a\n'}
            item['state']='captured' if item['open']['exit_code']==0 and item['screenshot']['exit_code']==0 and item.get('artifact',{}).get('png_signature') else 'failed'
            results.append(item);(out/'RESULTS.json').write_text(json.dumps(results,indent=2))
            print(engine,name,item['state'],flush=True)
    finally:
        (out/(engine+'-close.json')).write_text(json.dumps(command(argv+['close'],env,15),indent=2))
        if moli:
            if moli.poll() is None:
                moli.terminate()
                try:moli.wait(timeout=10)
                except subprocess.TimeoutExpired:moli.kill();moli.wait()
            log.close()
(out/'RESULTS.json').write_text(json.dumps(results,indent=2))
print('summary',json.dumps({state:sum(r['state']==state for r in results) for state in ['captured','failed','held']}),flush=True)

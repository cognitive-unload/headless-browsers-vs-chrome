"""Container-only runner. All browser actions use the pinned agent-browser CLI.
Runs one engine and one phase. No keys, model calls, saved state or uploads.
"""
import argparse, hashlib, json, os, pathlib, re, signal, subprocess, threading, time, urllib.parse, urllib.request
from PNG import compare, dimensions, UnsupportedPNG
from LOCAL_NETWORK import configure as configure_network, inspect_namespace
from PROCESS_SNAPSHOT import snapshot as process_snapshot
from SITE_POLICY import paint_decision, process_growth, current_pids

KIT=pathlib.Path('/opt/rig'); OUT=pathlib.Path('/out'); ROOT=pathlib.Path('/opt/headless')
ENV={'PATH':'/opt/headless/bin:/opt/rig/bin:/usr/local/bin:/usr/bin:/bin',
     'HOME':'/home/pwuser','TMPDIR':'/tmp','LANG':'C.UTF-8','TZ':'UTC',
     'LIGHTPANDA_DISABLE_TELEMETRY':'1','LIGHTPANDA_DISABLE_CORE_DUMP':'1',
     'AGENT_BROWSER_NO_VERSION_CHECK':'1','AGENT_BROWSER_DEFAULT_TIMEOUT':'45000',
     'SSL_CERT_FILE':'/opt/rig/ca-bundle.pem','CURL_CA_BUNDLE':'/opt/rig/ca-bundle.pem'}

class Unsupported(RuntimeError): pass
class ActionError(RuntimeError): pass

def append(name,value):
    with (OUT/name).open('a') as f: f.write(json.dumps(value)+'\n')

def execute(argv,timeout=50,env=ENV):
    begin=time.monotonic()
    before=process_snapshot()
    try:
        p=subprocess.run(argv,env=env,capture_output=True,text=True,timeout=timeout)
        result=dict(argv=argv,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except subprocess.TimeoutExpired:
        result=dict(argv=argv,exit=None,error='process deadline exceeded')
    except OSError as e:
        result=dict(argv=argv,exit=None,error=str(e),errno=e.errno,process_at_error=process_snapshot())
    result['process_before']=before
    result['seconds']=time.monotonic()-begin
    append('COMMANDS.jsonl',result)
    return result

class Agent:
    def __init__(self,engine,local_tls=False):
        self.engine=engine; self.server=None; self.log=None
        self.argv=['/opt/headless/bin/agent-browser','--json','--session','rig-'+engine]
        if engine=='chrome':
            self.argv+=['--executable-path',(ROOT/'CHROME_PATH.txt').read_text().strip()]
            if local_tls:self.argv+=['--args','--ignore-certificate-errors-spki-list='+ (KIT/'WPT_SPKI.txt').read_text().strip()]
        elif engine=='moli':
            self.log=(OUT/'moli.log').open('w')
            self.server=subprocess.Popen([str(ROOT/'bin/moli'),'serve','--host','127.0.0.1','--port','9222','--layout','--resource'],
                env=ENV,stdout=self.log,stderr=self.log,start_new_session=True)
            deadline=time.monotonic()+20
            while True:
                try:
                    with urllib.request.urlopen('http://127.0.0.1:9222/json/version',timeout=.5) as r: json.load(r)
                    break
                except Exception:
                    if self.server.poll() is not None or time.monotonic()>deadline: raise ActionError('Moli CDP start failed')
                    time.sleep(.1)
            self.argv+=['--cdp','http://127.0.0.1:9222']
        else: self.argv+=['--engine',engine,'--executable-path',str(ROOT/'bin'/engine)]
    def call(self,*args,timeout=50):
        if args and args[0] in ('press','key') and len(args)!=2:
            raise ActionError('press accepts exactly one key argument; focus via fill first')
        r=execute(self.argv+list(args),timeout)
        try: value=json.loads(r.get('stdout',''))
        except ValueError: value={}
        if r['exit']!=0 or value.get('success') is not True:
            error=str(value.get('error') or r)
            if re.search(r'not supported|not implemented|unknown method|method not found',error,re.I): raise Unsupported(error)
            raise ActionError(error)
        data=value.get('data',{})
        if args and args[0] in ('press','key') and data.get('pressed')!=args[1]:
            raise ActionError('key acknowledgement differs from requested key: '+str(data.get('pressed')))
        return data
    def evaluate(self,script): return self.call('eval',script).get('result')
    def geometry(self,w,h):
        self.call('set','viewport',str(w),str(h),'1')
        actual=self.evaluate('[innerWidth,innerHeight,devicePixelRatio]')
        if actual!=[w,h,1]: raise Unsupported('CSS geometry differs: '+str(actual))
    def ready(self,condition,seconds=45,reftest=False,check_blocks=True,diagnostics=False):
        # Deadline bounds a hung or incomplete site, not an arbitrary success delay.
        source=(KIT/'READY.js').read_text()
        ref=" && !document.documentElement.classList.contains('reftest-wait')" if reftest else ''
        expression=source+f'\n(async()=>!!({condition}) && !!(await rigPaintReady()){ref})()'
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            block=self.blocked() if check_blocks else None
            if block: return dict(state='bot-check',evidence=block)
            if diagnostics:
                probe_source=(KIT/'SITE_PROBE.js').read_text()
                probe=self.evaluate(probe_source+'\nrigSiteProbe(()=>('+condition+'))')
                append('READINESS.jsonl',dict(kind='site-readiness-probe',condition=condition,probe=probe))
                if probe.get('pageError'):raise ActionError('readiness condition error: '+probe['pageError'])
            if diagnostics:
                page_ready=bool(probe.get('pageReady'))
                # Preserve the existing short circuit and paint function. Observe
                # each part without treating a loaded-looking page as ready.
                paint_ready=bool(self.evaluate(source+'\n(async()=>!!(await rigPaintReady()))()')) if page_ready else None
                ready=page_ready and paint_ready
                append('READINESS.jsonl',dict(kind='site-readiness-result',condition=condition,page_ready=page_ready,paint_ready=paint_ready,combined_ready=bool(ready)))
            else:ready=bool(self.evaluate(expression))
            if ready: return dict(state='ready')
            time.sleep(.1)
        return dict(state='timeout',condition=condition)
    def site_ready(self,condition,seconds=45,legacy_clauses=(),defer_blocks=False):
        source=(KIT/'READY.js').read_text()
        probe_source=(KIT/'SITE_PROBE.js').read_text()
        clauses='['+','.join('{label:'+json.dumps(c['label'])+',check:()=>('+c['expression']+')}' for c in legacy_clauses)+']'
        deadline=time.monotonic()+seconds
        page_since=None
        while time.monotonic()<deadline:
            if not defer_blocks:
                block=self.blocked()
                if block:return dict(state='bot-check',evidence=block)
            probe=self.evaluate(probe_source+'\nrigSiteProbe(()=>('+condition+'),'+clauses+')')
            append('READINESS.jsonl',dict(kind='site-readiness-probe',condition=condition,probe=probe))
            if not isinstance(probe,dict):
                page_since=None;time.sleep(.1);continue
            if probe.get('pageError'):raise ActionError('readiness condition error: '+probe['pageError'])
            page_ready=bool(probe.get('pageReady'))
            now=time.monotonic()
            page_since=(now if page_since is None else page_since) if page_ready else None
            # Keep the original paint check; bound a pending fonts/rAF promise so
            # the reviewed 15-second observation policy remains reachable.
            paint_ready=bool(self.evaluate(source+'\nPromise.race([rigPaintReady(),new Promise(resolve=>setTimeout(()=>resolve(false),250))])')) if page_ready else None
            elapsed=time.monotonic()-page_since if page_since is not None else 0
            pending=probe.get('paint',{}).get('pendingVisibleImages',0)
            decision=paint_decision(page_ready,paint_ready,elapsed,pending)
            append('READINESS.jsonl',dict(kind='site-readiness-result',condition=condition,page_ready=page_ready,
                paint_ready=paint_ready,page_ready_elapsed=elapsed,combined_ready=decision is not None,decision=decision))
            if decision:
                if defer_blocks:
                    block=self.blocked()
                    if block:return dict(state='bot-check',evidence=block)
                decision['page_since']=page_since
                return decision
            time.sleep(.1)
        if defer_blocks:
            block=self.blocked()
            if block:return dict(state='bot-check',evidence=block)
        return dict(state='timeout',condition=condition)
    def blocked(self):
        return self.evaluate("(()=>{const t=(document.title+' '+(document.body?.textContent||'').slice(0,4000)); const m=t.match(/prove your humanity|verify (you are|you're) human|checking your browser|unusual traffic|robot check|automated access|access denied|blocked by network security|captcha/i);return m ? m[0] : null})()")
    def harness(self,seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            raw=self.evaluate('window.__rigWpt || null')
            if raw and raw.get('complete'): return raw
            time.sleep(.05)
        raise TimeoutError('testharness completion deadline exceeded')
    def shot(self,name,w=1280,h=720):
        actual=self.evaluate('[innerWidth,innerHeight,devicePixelRatio]')
        if actual!=[w,h,1]:raise Unsupported('CSS geometry before capture differs: '+str(actual))
        path=OUT/(name+'.png'); self.call('screenshot',str(path))
        raw=path.read_bytes()
        if dimensions(raw)!=(w,h): raise Unsupported('PNG geometry differs: '+str(dimensions(raw)))
        return dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),dimensions=[w,h])
    def close(self,strict=False):
        try: self.call('close',timeout=15)
        except Exception as e:
            append('CLOSE.jsonl',dict(error=str(e)))
            if strict:raise
        if self.server:
            if self.server.poll() is None:
                os.killpg(self.server.pid,signal.SIGTERM)
                try:self.server.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(self.server.pid,signal.SIGKILL);self.server.wait()
            self.log.close()

def status(raw):
    cases=[dict(t,state={0:'pass',1:'fail',2:'timeout',3:'not-run',4:'unsupported'}.get(t['status'],'not-run')) for t in raw['tests']]
    harness=raw['harness']['status']
    if harness==2 or any(t['state']=='timeout' for t in cases): state='timeout'
    elif harness not in (0,): state='unsupported' if harness==3 else 'fail'
    elif any(t['state']=='fail' for t in cases): state='fail'
    elif any(t['state']=='not-run' for t in cases): state='not-run'
    elif any(t['state']=='unsupported' for t in cases): state='unsupported'
    elif cases: state='pass'
    else: state='not-run'
    return dict(state=state,harness=raw['harness'],subtests=cases)

def wpt(agent):
    sample=json.loads((KIT/'WPT_SAMPLE.json').read_text())
    for index,test in enumerate(sample['tests']):
        item=dict(engine=agent.engine,index=index,area=test['area'],url=test['url'],kind=test['kind'],state='not-run')
        try:
            capabilities=json.loads((OUT/'PREFLIGHT_PASSED.json').read_text())
            if test['scheme']=='https' and capabilities.get('https-collector',{}).get('state')!='pass':
                raise Unsupported('HTTPS known-answer fixture did not pass; trust/protocol adapter unavailable')
            if test['kind']=='reftest' and capabilities.get('reftest-pixels',{}).get('state')!='pass':
                raise Unsupported('known-different pixel/reftest-wait fixture did not pass')
            if test['testdriver']: raise Unsupported('testdriver automation adapter unavailable; assertions not attempted')
            meta=test['metadata']
            if meta.get('viewport-size') or meta.get('fuzzy'): raise Unsupported('non-default viewport/fuzzy metadata needs upstream adapter')
            agent.geometry(800,600)
            base=test['scheme']+'://web-platform.test:'+('8443' if test['scheme']=='https' else '8000')
            url=base+test['url']; agent.call('open',url)
            if test['kind']=='testharness':
                item.update(status(agent.harness(60 if 'long' in meta.get('timeout',[]) else 15)))
                try:
                    readiness=agent.ready('true',15,check_blocks=False)
                    item['capture_ready']=readiness
                    if readiness['state']=='ready':item['screenshot']=agent.shot('wpt-'+str(index),800,600)
                except Exception as e:item['capture_error']=str(e)
            else:
                ready=agent.ready('true',15,check_blocks=False)
                if ready['state']!='ready': item.update(ready)
                else:
                    # Reftest readiness must precede reference navigation and capture.
                    agent.evaluate("document.documentElement.dispatchEvent(new Event('TestRendered',{bubbles:true}))")
                    ready=agent.ready('true',15,reftest=True,check_blocks=False)
                    if ready['state']!='ready': item.update(ready); continue
                    shot=agent.shot('wpt-'+str(index),800,600); item['screenshot']=shot
                    raw=(OUT/shot['file']).read_bytes(); matches=[]; mismatches=[]; item['references']=[]
                    for ri,(ref,relation) in enumerate(test['references']):
                        refurl=urllib.parse.urljoin(url,ref); agent.call('open',refurl)
                        if agent.evaluate("!!document.querySelector('link[rel=match],link[rel=mismatch],meta[name=fuzzy],meta[name=viewport-size]')"):
                            raise Unsupported('chained or fuzzy reference requires upstream adapter')
                        rr=agent.ready('true',15,reftest=True,check_blocks=False)
                        if rr['state']!='ready': raise TimeoutError('reference incomplete')
                        refshot=agent.shot('wpt-'+str(index)+'-ref-'+str(ri),800,600)
                        delta=compare(raw,(OUT/refshot['file']).read_bytes()); equal=delta['totalPixels']==0
                        (matches if relation=='match' else mismatches).append(equal)
                        item['references'].append(dict(url=refurl,relation=relation,delta=delta,screenshot=refshot))
                    item['state']='pass' if (not matches or any(matches)) and not any(mismatches) else 'fail'
        except Unsupported as e: item.update(state='unsupported',reason=str(e))
        except UnsupportedPNG as e: item.update(state='unsupported',reason='PNG adapter: '+str(e))
        except TimeoutError as e: item.update(state='timeout',reason=str(e))
        except Exception as e: item.update(state='not-run',reason='runner/transport error: '+str(e))
        finally: append('WPT.jsonl',item)

def record_start(agent,name):
    try: return dict(state='recording',result=agent.call('record','start',str(OUT/(name+'.webm')),'--fps','30'))
    except Exception as e:
        try:agent.call('record','stop',timeout=30)
        except Exception:pass
        return dict(state='unsupported',reason=str(e))

def record_stop(agent,record):
    if record['state']!='recording': return record
    try:
        data=agent.call('record','stop',timeout=30)
        record.update(state='recorded' if data.get('capturedFrames',0)>1 else 'insufficient-motion-frames',result=data)
        path=pathlib.Path(data.get('path',''))
        if path.is_file():
            record.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
            probe=execute(['ffmpeg','-hide_banner','-i',str(path),'-map','0:v:0','-f','framemd5','-'],timeout=45)
            hashes=[l.split(',')[-1].strip() for l in probe.get('stdout','').splitlines() if l and not l.startswith('#')]
            good_size=bool(re.search(r'Video:.*\b1280x720\b',probe.get('stderr','')))
            record.update(decoded_frames=len(hashes),distinct_frame_hashes=len(set(hashes)),dimensions_checked=good_size)
            if probe['exit']!=0 or not good_size or len(set(hashes))<2:record['state']='recording-validation-failed'
    except Exception as e: record.update(state='failed',reason=str(e))
    return record

def text_condition(rule):
    return '(()=>{'+(KIT/'SITE_TEXT.js').read_text()+'\nreturn rigTextReady('+json.dumps(rule)+');})()'

def site_viewport(agent,label):
    before=agent.evaluate('[innerWidth,innerHeight,devicePixelRatio]')
    agent.geometry(1280,720)
    append('VIEWPORT.jsonl',dict(label=label,before=before,after=[1280,720,1],state='verified'))

def prepare_visit(agent,label,previous_pids):
    before=process_snapshot();current=current_pids(before)
    growing=process_growth(previous_pids,current)
    append('SITE_PROCESS.jsonl',dict(label=label,point='start',previous_pids=previous_pids,current_pids=current,
        growing=growing,process=before))
    if growing:
        engine=agent.engine
        # A failed/uncertain close stops the phase, never launches a second copy.
        agent.close(strict=True);agent.__init__(engine)
        agent.call('open','about:blank');agent.geometry(1280,720)
        after=process_snapshot()
        append('SITE_PROCESS.jsonl',dict(label=label,point='after-session-reset',process=after))
        return current_pids(after)
    return current

def sites(agent,motion=False):
    plan=json.loads((KIT/'SITES.json').read_text()); agent.geometry(1280,720)
    previous_pids=None
    for site in plan['sites']:
        previous_pids=prepare_visit(agent,'site-'+site['id'],previous_pids)
        item=dict(engine=agent.engine,id=site['id'],url=site['url'],state='not-run')
        try:
            agent.call('open',site['url']);site_viewport(agent,'site-'+site['id'])
            result=agent.site_ready(text_condition(site['text_ready']),legacy_clauses=site['legacy_clauses']); item.update(result)
            # Timeout/block images are diagnostics, never successful rendered-page scores.
            item['screenshot']=agent.shot('site-'+site['id'])
            item['page_evidence']=agent.evaluate('({url:location.href,title:document.title,images:Array.from(document.images).map(i=>({src:i.currentSrc,complete:i.complete,width:i.naturalWidth})),viewport:[innerWidth,innerHeight,devicePixelRatio]})')
        except Unsupported as e: item.update(state='unsupported',reason=str(e))
        except Exception as e: item.update(state='not-run',reason=str(e))
        append('SITES.jsonl',item)
    for task in plan['tasks']:
        previous_pids=prepare_visit(agent,'task-'+task['id'],previous_pids)
        try:
            site=next(s for s in plan['sites'] if s['id']==task['id'])
            condition=text_condition(site['text_ready'])
            record=record_start(agent,'task-'+task['id']+'-open') if motion else dict(state='disabled')
            initial=dict(engine=agent.engine,id=task['id'],step='open',state='not-run')
            try:
                agent.call('open',task['start']);site_viewport(agent,'task-'+task['id']+'-open')
                first=agent.site_ready(condition,legacy_clauses=site['legacy_clauses'])
                initial.update(first);initial['screenshot']=agent.shot('task-'+task['id']+'-open')
            finally:
                initial['recording']=record_stop(agent,record) if motion else dict(state='disabled');append('TASKS.jsonl',initial)
            if first['state']!='ready':
                continue
            for step in task['steps']:
                for command_index,command in enumerate(step['commands']):
                    name='task-'+task['id']+'-'+step['id']+'-'+str(command_index)
                    record=record_start(agent,name) if motion else dict(state='disabled')
                    item=dict(engine=agent.engine,id=task['id'],step=step['id'],action=command,action_index=command_index,state='not-run')
                    try:
                        if command==['click-first-product']:
                            selector=agent.evaluate("(()=>{const e=document.querySelector('div[data-component-type=s-search-result][data-asin]:not([data-asin=\"\"]) h2 a') || document.querySelector('div[data-component-type=s-search-result] a:has(h2)');if(!e)return null;let a=[];for(let n=e;n&&n.nodeType===1;n=n.parentElement){let i=1;for(let p=n.previousElementSibling;p;p=p.previousElementSibling)i++;a.unshift(n.tagName.toLowerCase()+':nth-child('+i+')')}return a.join(' > ')})()")
                            if not selector: raise ActionError('No product link; no alternate page or bypass attempted')
                            agent.call('click',selector)
                        else: agent.call(*command)
                        condition=step['ready'] if command_index==len(step['commands'])-1 else 'true'
                        if command[0]=='fill':
                            condition='document.querySelector('+json.dumps(command[1])+')?.value === '+json.dumps(command[2])
                        site_viewport(agent,name)
                        defer_blocks=task['id']=='wikipedia' and step['id']=='second-result'
                        item.update(agent.site_ready(condition,defer_blocks=defer_blocks));item['screenshot']=agent.shot(name)
                        item['observed']=agent.evaluate('({url:location.href,title:document.title,heading:document.querySelector("h1")?.textContent})')
                    except Unsupported as e:item.update(state='unsupported',reason=str(e))
                    except Exception as e:item.update(state='not-run',reason=str(e))
                    finally:item['recording']=record_stop(agent,record) if motion else dict(state='disabled');append('TASKS.jsonl',item)
                    if item['state']!='ready':break
                if item['state']!='ready':break
        except Exception as e:append('TASKS.jsonl',dict(engine=agent.engine,id=task['id'],state='not-run',reason=str(e)))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--engine',choices=['chrome','lightpanda','obscura','moli'],required=True)
    parser.add_argument('--phase',choices=['preflight','wpt','sites','speed','benchmark'],required=True); args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if os.getuid()!=1000 or pathlib.Path('/.dockerenv').exists() is False: raise RuntimeError('container UID gate')
    network_env,network_receipt=configure_network(args.engine,args.phase,ENV,inspect_namespace())
    ENV.clear();ENV.update(network_env)
    (OUT/'LOCAL_NETWORK_POLICY.json').write_text(json.dumps(network_receipt,indent=2))
    if args.phase not in ('preflight','wpt'):
        ENV['SSL_CERT_FILE']='/etc/ssl/certs/ca-certificates.crt';ENV['CURL_CA_BUNDLE']=ENV['SSL_CERT_FILE']
    # Persist the full denominator even if instrumentation startup subsequently fails.
    if args.phase=='wpt':(OUT/'PLANNED_WPT.json').write_bytes((KIT/'WPT_SAMPLE.json').read_bytes())
    agent=Agent(args.engine,local_tls=args.phase in ('preflight','wpt'))
    try:
        agent.call('open','about:blank');agent.geometry(800 if args.phase=='wpt' else 1280,600 if args.phase=='wpt' else 720)
        from PREFLIGHT import run as preflight
        preflight(agent,require_collector=args.phase in ('preflight','wpt'),motion=args.phase=='preflight')
        if args.phase!='preflight':
            agent.close();agent=Agent(args.engine,local_tls=args.phase=='wpt')
            agent.call('open','about:blank')
            agent.geometry(800 if args.phase=='wpt' else 1280,600 if args.phase=='wpt' else 720)
        if args.phase=='wpt':
            (OUT/'PLANNED_WPT.json').write_bytes((KIT/'WPT_SAMPLE.json').read_bytes())
        else:(OUT/'PLANNED_SITES.json').write_bytes((KIT/'SITES.json').read_bytes())
        if args.phase=='wpt':wpt(agent)
        elif args.phase=='sites':
            sites(agent)
            from SITE_GATE import assess
            acceptance=assess(OUT,json.loads((KIT/'SITES.json').read_text()))
            (OUT/'SITE_ACCEPTANCE.json').write_text(json.dumps(acceptance,indent=2)+'\n')
            # An incomplete run stays explicit even if the process itself exits 0.
            # Only Chrome is the acceptance reference; other engines report their results.
        elif args.phase=='preflight':pass
        elif args.phase=='benchmark':
            from SPEED import Memory
            memory=Memory(agent.engine);memory.start()
            try:
                endpoint=agent.call('get','cdp-url')['cdpUrl']
                result=execute(['node','/opt/rig/BENCHMARK.mjs',endpoint],timeout=1200)
                if result['exit']!=0:append('BENCHMARK_STATUS.jsonl',dict(state='not-run',reason=result))
            finally:append('BENCHMARK_MEMORY.jsonl',dict(peak_process_tree_pss_kib=memory.finish()))
        else:
            from SPEED import run
            run(agent)
    finally:
        agent.close()
        from SUMMARIZE import run
        run(OUT,args.engine)
if __name__=='__main__':main()

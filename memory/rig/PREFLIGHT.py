"""Known-answer checks run only after review, in the locked test container."""
import json, pathlib
from RUN import append, record_start, record_stop, status
from PNG import compare

def run(agent,require_collector=True,motion=True):
    results={}
    for w,h in ((800,600),(1280,720)):
        try:
            agent.geometry(w,h); shot=agent.shot('geometry-'+str(w),w,h)
            results['geometry-'+str(w)]=dict(state='pass',screenshot=shot)
        except Exception as e:results['geometry-'+str(w)]=dict(state='unsupported',reason=str(e))
    for scheme,port in (('http',8000),('https',8443)):
        try:
            agent.call('open',f'{scheme}://web-platform.test:{port}/__rig/known.html')
            raw=agent.harness(15); outcome=status(raw)
            passed=sorted(t['state'] for t in outcome['subtests'])==['fail','pass']
            results[scheme+'-collector']=dict(state='pass' if passed else 'instrumentation-error',raw=raw)
        except Exception as e:results[scheme+'-collector']=dict(state='unsupported',reason=str(e))
    try:
        agent.geometry(800,600);images=[]
        for color in ('red','blue'):
            agent.call('open','http://web-platform.test:8000/__rig/'+color+'.html')
            if agent.ready('true',15)['state']!='ready':raise RuntimeError('fixture paint not ready')
            agent.evaluate("document.documentElement.dispatchEvent(new Event('TestRendered',{bubbles:true}))")
            if agent.ready('true',15,reftest=True)['state']!='ready':raise RuntimeError('reftest-wait not released')
            shot=agent.shot('fixture-'+color,800,600);images.append((pathlib.Path('/out')/shot['file']).read_bytes())
        delta=compare(images[0],images[1]);equal=compare(images[0],images[0])
        results['reftest-pixels']=dict(state='pass' if delta['totalPixels']>0 and equal['totalPixels']==0 else 'unsupported',different=delta,identical=equal)
    except Exception as e:results['reftest-pixels']=dict(state='unsupported',reason=str(e))
    if not motion:
        results['motion']=dict(state='not-attempted',reason='no encoder started in WPT/performance jobs')
        append('PREFLIGHT.jsonl',dict(engine=agent.engine,checks=results))
        if require_collector and results['http-collector']['state']!='pass':raise RuntimeError('collector preflight failed')
        (pathlib.Path('/out')/'PREFLIGHT_PASSED.json').write_text(json.dumps(results,indent=2))
        return
    recording=None
    try:
        agent.geometry(1280,720);agent.call('open','http://web-platform.test:8000/__rig/motion.html')
        recording=record_start(agent,'motion-preflight')
        agent.call('click','#move')
        # Bounded wait for the fixture's own animation completion, no guessed delay.
        agent.call('wait','--fn','window.motionDone === true')
        results['motion']=dict(state='ready')
        results['motion']['screenshot']=agent.shot('motion-after')
    except Exception as e:results['motion']=dict(state='unsupported',reason=str(e))
    finally:
        if recording:results.setdefault('motion',{})['recording']=record_stop(agent,recording)
    append('PREFLIGHT.jsonl',dict(engine=agent.engine,checks=results))
    # A positive HTTP collector known-answer check is required for scoring tests.
    if require_collector and results['http-collector']['state']!='pass': raise RuntimeError('collector preflight did not pass; WPT scoring held')
    (pathlib.Path('/out')/'PREFLIGHT_PASSED.json').write_text(json.dumps(results,indent=2))

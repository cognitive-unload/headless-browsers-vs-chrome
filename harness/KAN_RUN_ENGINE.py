"""Host supervisor: offline fixture and read-only per-step SQL observations."""
import importlib.util,json,os,pathlib,subprocess,sys,threading,time
ROOT=pathlib.Path(os.environ['KAN_ROOT']);EDIT=pathlib.Path(os.environ['KAN_HARNESS_DIR'])
engine=sys.argv[1] if len(sys.argv)>1 else 'chrome'
assert engine in ['chrome','obscura','moli','lightpanda']
if engine!='chrome':
    gate=json.loads((ROOT/'fixture-chrome/out/RESULT.json').read_text());assert gate['passed']==11 and gate['failure'] is None
subprocess.run(['python3',str(EDIT/'KAN_FIXTURE.py'),'up',engine],check=True)
folder=ROOT/('fixture-'+engine);out=folder/'out';done=threading.Event()
def witness():
    last=0
    while not done.is_set():
        try:
            n=json.loads((out/'ORACLE_REQUEST.json').read_text())['sequence']
            if n!=last:
                raw=subprocess.check_output(['python3',str(EDIT/'KAN_FIXTURE.py'),'observe',engine])
                temp=out/'ORACLE_RESPONSE.tmp';temp.write_text(json.dumps({'sequence':n,'state':json.loads(raw)}));temp.chmod(0o644);temp.replace(out/'ORACLE_RESPONSE.json');last=n
        except FileNotFoundError:pass
        except Exception as e:(folder/'WITNESS_ERROR.txt').write_text(str(e))
        time.sleep(.05)
t=threading.Thread(target=witness,daemon=True);t.start()
try:
    with (folder/'RUN.log').open('w') as log:subprocess.run(['docker','exec','kan-fixture-'+engine+'-browser','python3','/opt/kan-capture/KAN_CAPTURE.py',engine],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=900)
finally:
    done.set();t.join(timeout=5)
    for service in ['web','pg']:
        p=subprocess.run(['docker','logs','kan-fixture-'+engine+'-'+service],capture_output=True)
        (folder/(service.upper()+'.log')).write_bytes(p.stdout+p.stderr)
    subprocess.run(['python3',str(EDIT/'KAN_FIXTURE.py'),'down',engine],check=True)
print((out/'RESULT.json').read_text())

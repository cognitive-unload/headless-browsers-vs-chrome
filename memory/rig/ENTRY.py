"""Start local services, validate environment, then one engine/phase."""
import json, os, pathlib, signal, socket, subprocess, sys, time, urllib.request
from SERVICE_HEALTH import check as service_health
from IMAGE_CHECK import check as image_check

def main():
    out=pathlib.Path('/out');out.mkdir(exist_ok=True)
    (out/'ENGINE_BINARIES_RECEIPT.json').write_text(json.dumps(image_check(pathlib.Path('/opt/headless'),json.loads(pathlib.Path('/opt/rig/ENGINE_BINARIES.json').read_text())),indent=2))
    services=[];logs=[];runner=None
    try:
        for name in ('DNS','SERVER'):
            log=(out/(name+'.log')).open('w');logs.append(log)
            services.append(subprocess.Popen(['/usr/bin/python3','/opt/rig/'+name+'.py'],stdout=log,stderr=log,start_new_session=True))
        log=(out/'DEMO.log').open('w');logs.append(log)
        services.append(subprocess.Popen(['/usr/bin/python3','-m','http.server','1234','--bind','127.0.0.1','--directory','/opt/demo'],stdout=log,stderr=log,start_new_session=True))
        deadline=time.monotonic()+40
        while True:
            try:
                health=service_health()
                break
            except Exception:
                if any(p.poll() is not None for p in services) or time.monotonic()>deadline:raise RuntimeError('Local WPT/DNS startup failed')
                time.sleep(.2)
        (out/'SERVICE_HEALTH.json').write_text(json.dumps(dict(state='pass',checks=health),indent=2))
        try:
            telemetry={r[4][0] for r in socket.getaddrinfo('telemetry.lightpanda.io',443)}
            if not telemetry.issubset({'127.0.0.1','::1','0.0.0.0'}):raise RuntimeError('Telemetry hostname unexpectedly resolved externally')
        except socket.gaierror:telemetry=set()
        # Record only names of environment variables, never inherited values.
        (out/'ISOLATION.json').write_text(json.dumps(dict(uid=os.getuid(),environment_names=sorted(os.environ),
            telemetry_resolution=sorted(telemetry) or 'NXDOMAIN',test_dns=socket.gethostbyname('www.web-platform.test'),published_ports=False,
            note='own containment check; not a packet-capture or engine telemetry-attempt observation'),indent=2))
        runner=subprocess.Popen(['/usr/bin/python3','/opt/rig/RUN.py']+sys.argv[1:],start_new_session=True)
        while runner.poll() is None:
            if any(p.poll() is not None for p in services):raise RuntimeError('Local service exited during engine phase; results are incomplete')
            time.sleep(.1)
        if any(p.poll() is not None for p in services):raise RuntimeError('Local service exited before phase completion')
        if runner.returncode:raise subprocess.CalledProcessError(runner.returncode,runner.args)
        final_health=service_health()
        (out/'SERVICE_HEALTH_FINAL.json').write_text(json.dumps(dict(state='pass',services_alive=True,checks=final_health),indent=2))
    finally:
        if runner is not None and runner.poll() is None:
            os.killpg(runner.pid,signal.SIGTERM)
            try:runner.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(runner.pid,signal.SIGKILL);runner.wait()
        for p in services:
            if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
        for p in services:
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        for log in logs:log.close()
if __name__=='__main__':main()

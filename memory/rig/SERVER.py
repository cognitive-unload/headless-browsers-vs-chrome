"""Call audited WPT serving modules directly: no wpt CLI/venv/pip bootstrap."""
import pathlib, sys
ROOT=pathlib.Path('/opt/wpt')
sys.path[:0]=['/opt/rig/python',str(ROOT/'tools'),str(ROOT/'tools/wptserve')]
if __name__=='__main__':
    from serve.serve import run
    raise SystemExit(run(config_path='/opt/rig/WPT_CONFIG.json',h2=True,webtransport_h3=False,dns=False))

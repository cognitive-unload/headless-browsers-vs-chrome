"""Use the frozen CLI adapter for observed UI setup and capture commands."""
import json,pathlib,sys
sys.path.insert(0,'/opt/rig')
import RUN
from LOCAL_NETWORK import inspect_namespace,require_isolated
from IMAGE_CHECK import check
require_isolated(inspect_namespace())
engine=sys.argv[1]
if engine=='obscura':RUN.ENV['OBSCURA_ALLOW_PRIVATE_NETWORK']='1'
agent=RUN.Agent(engine)
args=json.loads(sys.argv[2])
if args==['verify']:
    result={'isolation':inspect_namespace(),'binaries':check(pathlib.Path('/opt/headless'),json.loads(pathlib.Path('/opt/rig/ENGINE_BINARIES.json').read_text()))}
elif args and args[0]=='shot':result=agent.shot(args[1],int(args[2]) if len(args)>2 else 1280,720)
else:result=agent.call(*args)
print(json.dumps(result))

import os,pathlib,sys,time
sys.path.insert(0,'/opt/rig')
import RUN
from LOCAL_NETWORK import inspect_namespace,require_isolated
require_isolated(inspect_namespace())
a=RUN.Agent('chrome')
for args in [('fill','input[placeholder="Enter your name"]','Capture User'),('fill','input[placeholder="Enter your email address"]','capture@example.test'),('fill','input[placeholder="Enter your password"]',os.environ['KAN_TEST_PASSWORD']),('click','button:has-text("Sign up with email")')]:a.call(*args)
until=time.monotonic()+30
while not a.evaluate('!!document.querySelector("input[placeholder=\\"Workspace name\\"]")'):
    if time.monotonic()>until:raise RuntimeError('Workspace onboarding not reached')
    time.sleep(.1)
a.call('fill','input[placeholder="Workspace name"]','Capture workspace')
a.call('click','button:has-text("Create workspace")')
until=time.monotonic()+30
while not a.evaluate('location.pathname==="/boards" && !document.querySelector("input[placeholder=\\"Workspace name\\"]")'):
    if time.monotonic()>until:raise RuntimeError('Workspace creation not completed')
    time.sleep(.1)
a.call('screenshot','/out/SEED_UI.png')
print(a.call('snapshot'))
a.close()

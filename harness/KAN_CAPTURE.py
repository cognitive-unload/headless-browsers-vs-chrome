"""Same fixed eleven UI steps for every engine; observational file oracle."""
import json,os,pathlib,sys,time,traceback
sys.path.insert(0,'/opt/rig')
import RUN
from LOCAL_NETWORK import inspect_namespace,require_isolated
from IMAGE_CHECK import check
OUT=pathlib.Path('/out');engine=sys.argv[1];BASE='http://127.0.0.1:3000'
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
require_isolated(inspect_namespace())
save('ISOLATION.json',inspect_namespace())
save('ENGINE_HASHES.json',check(pathlib.Path('/opt/headless'),json.loads(pathlib.Path('/opt/rig/ENGINE_BINARIES.json').read_text())))
if engine=='obscura':RUN.ENV['OBSCURA_ALLOW_PRIVATE_NETWORK']='1'
agent=RUN.Agent(engine);steps=[];oracle_seq=0
def oracle():
    global oracle_seq
    oracle_seq+=1;n=oracle_seq
    save('ORACLE_REQUEST.json',{'sequence':n})
    for _ in range(100):
        try:
            r=json.loads((OUT/'ORACLE_RESPONSE.json').read_text())
            if r['sequence']==n:return r['state']
        except (FileNotFoundError,json.JSONDecodeError):pass
        time.sleep(.1)
    raise RuntimeError('Read-only database oracle deadline')
def wait(expr,seconds=30):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if agent.evaluate('!!('+expr+')') is True:return
        time.sleep(.1)
    raise RUN.ActionError('App observation deadline: '+expr)
def state_wait(predicate,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        s=oracle()
        if predicate(s):return s
        time.sleep(.2)
    raise RUN.ActionError('Persisted-state observation deadline; last='+json.dumps(s))
def page():return agent.evaluate('({url:location.href,text:document.body?.innerText,viewport:[innerWidth,innerHeight,devicePixelRatio],dark:document.documentElement.classList.contains("dark")})')
def shot(name,width=1280):
    try:return {'capture':agent.shot(name,width,720)}
    except Exception as e:
        save(name+'-TEXT.json',page());return {'capture_error':str(e),'text_capture':name+'-TEXT.json'}
def named_button(name):
    expression='(()=>{const e=[...document.querySelectorAll("button")].find(e=>e.textContent.trim()==='+json.dumps(name)+' && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0 && !e.disabled);if(!e)return null;if(e.id)return "#"+CSS.escape(e.id);let p=e,s=[];while(p&&p.tagName!=="HTML"){let n=1,q=p;while(q=q.previousElementSibling)if(q.tagName===p.tagName)n++;s.unshift(p.tagName.toLowerCase()+":nth-of-type("+n+")");p=p.parentElement;}return s.join(" > ")})()'
    wait(expression)
    selector=agent.evaluate(expression)
    agent.call('click',selector)
def calls(*rows):
    for row in rows:
        if row[:4]==('find','role','button','click'):named_button(row[5])
        else:agent.call(*row)
def step(name,action,expr,predicate=None,width=1280):
    row={'number':len(steps)+1,'name':name}
    try:
        action();wait(expr)
        row['database']=state_wait(predicate) if predicate else oracle()
        row['page']=page();row['action']='done'
    except Exception as e:
        row.update(action='failed',error=str(e))
        try:row.update(page=page(),database=oracle())
        except Exception as e2:row['observation_error']=str(e2)
    row.update(shot(f'{len(steps)+1:02d}-{name}',width));steps.append(row);save('STEPS.json',steps)
    if row['action']!='done' or (engine=='chrome' and row.get('capture_error')):raise RUN.ActionError('Stop dependent path after '+name)
def login():
    calls(('fill','input[placeholder="Enter your email address"]','capture@example.test'),('fill','input[placeholder="Enter your password"]',os.environ['KAN_TEST_PASSWORD']),('find','role','button','click','--name','Continue with email','--exact'))
    wait('location.pathname==="/boards" && [...document.querySelectorAll("button")].some(e=>e.textContent.trim()==="Capture User")')

def create_board():
    named_button('New')
    wait('document.querySelector("input[placeholder=\\\"Name\\\"]")')
    calls(('fill','input[placeholder="Name"]','Release planning'),('find','role','button','click','--name','Create board','--exact'))
def create_list(name):
    named_button('New list')
    wait('document.querySelector("input[placeholder=\\\"List name\\\"]")')
    calls(('fill','input[placeholder="List name"]',name),('find','role','button','click','--name','Create list','--exact'))
def create_card(title):
    agent.call('find','nth','0','div[data-board-draggable] button[aria-label="Add card"]','click')
    wait('document.querySelector("input[placeholder=\\\"Card title\\\"]")')
    calls(('fill','input[placeholder="Card title"]',title),('find','role','button','click','--name','Create card','--exact'))
def drag():
    selectors=agent.evaluate('(()=>{const card=[...document.querySelectorAll("a[data-board-draggable]")].find(e=>e.textContent.includes("Check mobile layout"));const list=document.querySelectorAll("[data-list-scroll-id]")[1];return {source:card?"a[href="+JSON.stringify(card.getAttribute("href"))+"]":null,target:list?"[data-list-scroll-id="+JSON.stringify(list.getAttribute("data-list-scroll-id"))+"]":null}})()')
    if not selectors['source'] or not selectors['target']:raise RUN.ActionError('Drag endpoints absent')
    agent.call('drag',selectors['source'],selectors['target'])
def edit():
    calls(('fill','#title','Check mobile layout — reviewed'),('click','.tiptap[contenteditable="true"]'),('type','.tiptap[contenteditable="true"]','Phone layout reviewed at 360px.'),('click','#title'))
def phone():
    calls(('click','a[aria-label="Close"]'))
    wait('location.pathname.startsWith("/boards/")')
    agent.geometry(360,720);agent.call('reload')
try:
    save('BASELINE.json',oracle())
    agent.call('open',BASE+'/login')
    try:save('THEME_SETUP.json',{'command':agent.call('set','media','dark')})
    except Exception as e:save('THEME_SETUP.json',{'error':str(e),'core_path_continues':True})
    agent.geometry(1280,720);wait('document.querySelector("input[type=password]")')
    save('INITIAL_CAPTURE.json',shot('00-login'))
    step('sign-in',login,'location.pathname==="/boards"')
    step('create-board',create_board,'/^\\/boards\\/[^/]+$/.test(location.pathname)',lambda s:len(s['boards'] or [])==1)
    step('add-list-1',lambda:create_list('To do'),'document.querySelectorAll("input[aria-label=\\"List name\\"]").length===1',lambda s:len(s['lists'] or [])==1)
    step('add-list-2',lambda:create_list('Done'),'document.querySelectorAll("input[aria-label=\\"List name\\"]").length===2',lambda s:len(s['lists'] or [])==2)
    for i,title in enumerate(['Check mobile layout','Record UI walkthrough','Review browser results'],1):
        step('add-card-'+str(i),lambda t=title:create_card(t),f'document.querySelectorAll("a[data-board-draggable]").length==={i}',lambda s,n=i:len(s['cards'] or [])==n)
    step('drag-card',drag,'document.querySelectorAll("[data-list-scroll-id]")[1]?.textContent.includes("Check mobile layout")',lambda s:any(c['title']=='Check mobile layout' and c['listId']==next(l['id'] for l in s['lists'] if l['name']=='Done') for c in s['cards']))
    step('open-card-dialog',lambda:agent.call('click',agent.evaluate('(()=>{const a=[...document.querySelectorAll("a[data-board-draggable]")].find(e=>e.textContent.includes("Check mobile layout"));return "a[href="+JSON.stringify(a.getAttribute("href"))+"]"})()')),'location.pathname.startsWith("/cards/") && document.querySelector("#title")')
    step('edit-card-dialog',edit,'document.querySelector("#title")?.value==="Check mobile layout — reviewed"',lambda s:any(c['title']=='Check mobile layout — reviewed' and 'Phone layout reviewed at 360px.' in (c['description'] or '') for c in s['cards']))
    step('phone-board',phone,'innerWidth===360 && document.querySelectorAll("a[data-board-draggable]").length===3',width=360)
except Exception as error:
    save('STOP.json',{'error':str(error),'traceback':traceback.format_exc()})
finally:
    if steps and steps[-1]['name']!='phone-board':
        try:
            agent.geometry(360,720);save('PHONE_AT_STOP.json',{'page':page(),**shot('phone-at-stop',360)})
        except Exception as e:save('PHONE_AT_STOP.json',{'error':str(e)})
    try:save('FINAL_DATABASE.json',oracle())
    except Exception as e:save('FINAL_DATABASE_ERROR.json',str(e))
    agent.close();save('RESULT.json',{'engine':engine,'passed':sum(s['action']=='done' for s in steps),'attempted':len(steps),'total':11,'failure':next((s for s in steps if s['action']!='done'),None)})

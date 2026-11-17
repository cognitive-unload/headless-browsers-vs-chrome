"""One engine at a time; repeated site readiness timings and sampled process PSS."""
import json, os, pathlib, threading, time
from RUN import KIT, OUT, append

class Memory:
    def __init__(self,engine):self.engine=engine;self.stop=threading.Event();self.thread=threading.Thread(target=self.loop);self.rows=[]
    def start(self):self.thread.start()
    def finish(self):self.stop.set();self.thread.join();return max((r['pss_kib'] for r in self.rows),default=None)
    def loop(self):
        while not self.stop.is_set():
            processes={}; roots=set()
            for p in pathlib.Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try:
                    exe=os.readlink(p/'exe');stat=(p/'stat').read_text().rsplit(')',1)[1].split()
                    processes[int(p.name)]=(int(stat[1]),p,exe)
                    if (self.engine=='chrome' and exe.endswith('/chrome')) or exe=='/opt/headless/bin/'+self.engine:roots.add(int(p.name))
                except (OSError,ValueError):pass
            descendants=set(roots)
            while True:
                new={pid for pid,(ppid,_,_) in processes.items() if ppid in descendants}-descendants
                if not new:break
                descendants.update(new)
            total=0; missing=[]
            for pid in descendants:
                try:
                    lines=(processes[pid][1]/'smaps_rollup').read_text().splitlines()
                    total+=int(next(l for l in lines if l.startswith('Pss:')).split()[1])
                except (OSError,StopIteration):missing.append(pid)
            row=dict(monotonic=time.monotonic(),pss_kib=total if descendants else None,pids=sorted(descendants),missing=missing)
            if row['pss_kib'] is not None:self.rows.append(row)
            append('MEMORY.jsonl',row);self.stop.wait(.1)

def run(agent):
    plan=json.loads((KIT/'SITES.json').read_text());agent.geometry(1280,720)
    memory=Memory(agent.engine);memory.start()
    try:
        for repetition in range(3):
            # Every engine receives the same order for a given repetition.
            rotation=repetition % len(plan['sites'])
            ordered=plan['sites'][rotation:]+plan['sites'][:rotation]
            for site in ordered:
                item=dict(engine=agent.engine,site=site['id'],repetition=repetition,cache='fresh-container-first-pass' if repetition==0 else 'warm-profile',state='not-run')
                begin=time.monotonic()
                try:agent.call('open',site['url']);item.update(agent.ready(site['ready']))
                except Exception as e:item['reason']=str(e)
                item['seconds_including_driver']=time.monotonic()-begin
                append('SPEED.jsonl',item)
    finally:
        peak=memory.finish();append('SPEED_SUMMARY.jsonl',dict(engine=agent.engine,peak_process_tree_pss_kib=peak,
            sampling_ms=100,recording=False,screenshots=False,scope='browser tree; WPT server and driver excluded; not exact vendor benchmark'))

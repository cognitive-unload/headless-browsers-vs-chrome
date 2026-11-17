"""Join the frozen denominator to append-only outcomes, including interrupted runs."""
import collections, json, pathlib
STATES=('pass','fail','timeout','not-run','unsupported')
def run(out,engine):
    planned=out/'PLANNED_WPT.json'
    if not planned.exists():return
    tests=json.loads(planned.read_text())['tests']; latest={}
    if (out/'WPT.jsonl').exists():
        for line in (out/'WPT.jsonl').read_text().splitlines():
            try:r=json.loads(line);latest[r['index']]=r
            except ValueError:pass
    rows=[latest.get(i,dict(engine=engine,index=i,area=t['area'],url=t['url'],state='not-run',reason='no completed runner receipt')) for i,t in enumerate(tests)]
    areas={}
    for area in {t['area'] for t in tests}:
        counts={s:sum(r['area']==area and r['state']==s for r in rows) for s in STATES}
        areas[area]=dict(planned=sum(counts.values()),counts=counts,pass_over_planned=counts['pass']/sum(counts.values()))
    (out/'WPT_SUMMARY.json').write_text(json.dumps(dict(engine=engine,areas=areas,results=rows,
        label='Selected HTML-only WPT sample; includes tentative tests; not full WPT conformance'),indent=2))
if __name__=='__main__':
    import sys
    run(pathlib.Path(sys.argv[1]),sys.argv[2])

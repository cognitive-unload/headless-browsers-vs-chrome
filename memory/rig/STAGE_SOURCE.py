"""Read source archives only. Never imports or executes downloaded code."""
import hashlib, json, pathlib, tarfile
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / 'staged'
PIN = 'b62c4db0c515e8aa6f104f589c19bd2cb9b3424d'
GROUPS = {
    'layout': ['css/css-grid/', 'css/css-flexbox/'],
    'fonts-images': ['css/css-fonts/', 'html/semantics/embedded-content/the-img-element/'],
    'canvas': ['html/canvas/element/'],
    'web-components': ['custom-elements/', 'shadow-dom/'],
    'network-storage': ['fetch/api/', 'webstorage/'],
}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(); self.harness = False; self.refs = []; self.meta = {}; self.driver = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script':
            self.harness |= a.get('src', '').endswith('/testharness.js')
            self.driver |= 'testdriver' in a.get('src', '')
        if tag == 'link' and a.get('rel') in ('match', 'mismatch'):
            self.refs.append([a['href'], a['rel']])
        if tag == 'meta' and a.get('name'):
            self.meta.setdefault(a['name'], []).append(a.get('content', ''))

def main():
    archive = EVIDENCE / 'source/WPT.tar.gz'
    candidates = {p: [] for ps in GROUPS.values() for p in ps}
    tools = EVIDENCE / 'source/wpt'
    with tarfile.open(archive) as tf:
        for member in tf:
            path = member.name.partition('/')[2]
            if member.isfile() and path.startswith('tools/'):
                dest = tools / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tf.extractfile(member).read())
            prefix = next((p for p in candidates if path.startswith(p)), None)
            if not prefix or not member.isfile() or not path.endswith(('.html', '.xhtml', '.xht')):
                continue
            if any(x in path.split('/') for x in ('resources', 'support', 'reference', 'reftests-ref')):
                continue
            raw = tf.extractfile(member).read()
            m = Metadata(); m.feed(raw.decode('utf-8', errors='replace'))
            if not (m.harness or m.refs) or '-manual.' in path or '-print.' in path:
                continue
            for variant in m.meta.get('variant', ['']):
                url = '/' + path + variant
                candidates[prefix].append(dict(url=url, source=path,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    kind='testharness' if m.harness else 'reftest',
                    references=m.refs, metadata=m.meta, testdriver=m.driver,
                    scheme='https' if '.https.' in path else 'http'))
    sample = []
    for area, prefixes in GROUPS.items():
        count = 40 // len(prefixes)
        for prefix in prefixes:
            ordered = sorted(candidates[prefix], key=lambda x: hashlib.sha256(
                ('headless-browser-20261109\0' + x['url']).encode()).hexdigest())
            for item in ordered[:count]:
                sample.append(dict(area=area, **item))
    plan = dict(commit=PIN, source_url=f'https://github.com/web-platform-tests/wpt/commit/{PIN}',
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        selection='40 per area; equal prefix quotas; SHA256(seed + NUL + URL), HTML testharness/reftests only; no worker-only or generated .any.js coverage',
        candidate_counts={k: len(v) for k,v in candidates.items()}, tests=sample)
    (HERE / 'WPT_SAMPLE.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps(dict(tests=len(sample), areas={a: sum(t['area']==a for t in sample) for a in GROUPS},
        kinds={k: sum(t['kind']==k for t in sample) for k in ('testharness', 'reftest')})))

if __name__ == '__main__': main()

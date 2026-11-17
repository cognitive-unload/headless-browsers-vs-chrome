"""Cache the real upstream font as immutable data for an offline Next build."""
import hashlib,json,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'font-input';DEST.mkdir(exist_ok=True)
url='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200..800&display=swap'
req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36'})
with urllib.request.urlopen(req,timeout=45) as response:css=response.read().decode()
(DEST/'ORIGINAL.css').write_text(css)
receipts=[]
for fonturl in sorted(set(re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)',css))):
    with urllib.request.urlopen(fonturl,timeout=45) as response:data=response.read()
    digest=hashlib.sha256(data).hexdigest();name=digest+'.woff2'
    (DEST/name).write_bytes(data)
    css=css.replace(fonturl,'/opt/kan-build/fonts/'+name)
    receipts.append({'url':fonturl,'file':name,'sha256':digest,'bytes':len(data)})
assert receipts
(DEST/'mock.cjs').write_text('module.exports = '+json.dumps({url:css})+';\n')
(DEST/'RECEIPT.json').write_text(json.dumps({'css_url':url,'files':receipts,'purpose':'unmodified real font data; offline build setting only'},indent=2)+'\n')
print('font assets',len(receipts))

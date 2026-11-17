"""First admission: official HTTPS metadata MD5/CRC32C then SHA256 pin."""
import base64,hashlib,json,os,pathlib,shutil,urllib.request
kit=pathlib.Path(__file__).resolve().parent
manifest=json.loads((kit/'ARTIFACTS.json').read_text())
asset=next(a for a in manifest['assets'] if a['name']=='chrome-linux64.zip')
scratch=pathlib.Path(os.environ['HEAVY_JOB_SCRATCH_DIR'])/'headless-smoke-20261109-r1'
scratch.mkdir(parents=True,exist_ok=True)
metadata_url=asset['publisher_metadata']+'?generation=1793667047341974'
with urllib.request.urlopen(metadata_url,timeout=60) as response:metadata=json.load(response)
assert metadata['generation']=='1793667047341974'
assert metadata['md5Hash']==asset['publisher_md5_base64']
assert metadata['crc32c']==asset['publisher_crc32c_base64']
(scratch/'CHROME_GOOGLE_METADATA.json').write_text(json.dumps(metadata,indent=2))
archive=scratch/asset['name']
if not archive.exists():
    with urllib.request.urlopen(asset['url'],timeout=120) as response,archive.open('wb') as output:shutil.copyfileobj(response,output)
table=[]
for index in range(256):
    value=index
    for bit in range(8):value=(value>>1)^ (0x82F63B78 if value&1 else 0)
    table.append(value)
def update(crc,chunk):
    for byte in chunk:crc=table[(crc^byte)&255]^(crc>>8)
    return crc
assert (update(0xffffffff,b'123456789')^0xffffffff)==0xe3069283
md5=hashlib.md5();sha=hashlib.sha256();crc=0xffffffff
with archive.open('rb') as source:
    for chunk in iter(lambda:source.read(1024*1024),b''):
        md5.update(chunk);sha.update(chunk);crc=update(crc,chunk)
actual_md5=base64.b64encode(md5.digest()).decode()
actual_crc=base64.b64encode((crc^0xffffffff).to_bytes(4,'big')).decode()
assert archive.stat().st_size==int(metadata['size'])
assert actual_md5==metadata['md5Hash'],'MD5 mismatch'
assert actual_crc==metadata['crc32c'],'CRC32C mismatch'
computed=sha.hexdigest()
if asset.get('sha256'):assert asset['sha256']==computed,'previous SHA256 pin mismatch'
asset['sha256']=computed
asset['sha256_origin']='Computed locally after Google HTTPS MD5 and CRC32C matches; not publisher SHA256'
(kit/'ARTIFACTS.json').write_text(json.dumps(manifest,indent=2)+'\n')
receipt={'version':asset['version'],'url':asset['url'],'metadata_url':metadata_url,'generation':metadata['generation'],'size':archive.stat().st_size,'md5_base64':actual_md5,'crc32c_base64':actual_crc,'computed_sha256':computed,'md5_match':True,'crc32c_match':True,'owner_approval':asset['owner_approval'],'crc32c_test_vector':'123456789=e3069283'}
(scratch/'CHROME_INTEGRITY.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Chrome verified MD5 + CRC32C; pinned SHA256',computed,flush=True)

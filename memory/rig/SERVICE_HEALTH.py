"""Container-only protocol known answers, before any engine launches."""
import base64, hashlib, socket, ssl, urllib.request

def exact(sock,n):
    value=b''
    while len(value)<n:
        data=sock.recv(n-len(value))
        if not data:raise RuntimeError('fixture connection ended early')
        value+=data
    return value

def websocket(port,context=None):
    raw=socket.create_connection(('127.0.0.1',port),timeout=2)
    conn=context.wrap_socket(raw,server_hostname='web-platform.test') if context else raw
    with conn:
        key='cmlnLWZpeHR1cmUta2V5IQ=='
        request=('GET /echo HTTP/1.1\r\nHost: web-platform.test:'+str(port)+'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '+key+'\r\nSec-WebSocket-Version: 13\r\n\r\n').encode()
        conn.sendall(request);response=b''
        while not response.endswith(b'\r\n\r\n'):
            if len(response)>8192:raise RuntimeError('fixture upgrade headers too large')
            response+=exact(conn,1)
        expected=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        if b' 101 ' not in response.split(b'\r\n')[0] or expected.lower() not in response.lower():raise RuntimeError('WebSocket upgrade failed')
        payload=b'rig-fixture';mask=b'mask'
        conn.sendall(bytes([0x81,0x80|len(payload)])+mask+bytes(v^mask[i%4] for i,v in enumerate(payload)))
        if exact(conn,2)!=bytes([0x81,len(payload)]) or exact(conn,len(payload))!=payload:raise RuntimeError('WebSocket echo differs')
        conn.sendall(b'\x88\x80'+mask)
    return 'upgrade-and-echo-pass'

def check():
    results={}
    for port in (8000,8001,8002,8003,8443,8444,8445,8446,9000,8888,8889):
        with socket.create_connection(('127.0.0.1',port),timeout=2):pass
        results[str(port)]='listening'
    context=ssl.create_default_context(cafile='/opt/wpt/tools/certs/cacert.pem')
    for scheme,port in (('http',8000),('https',8443)):
        with urllib.request.urlopen(f'{scheme}://web-platform.test:{port}/__rig/known.html',timeout=2,context=context) as response:
            if response.status!=200 or b'known pass' not in response.read():raise RuntimeError('HTTP fixture differs')
        results[scheme]='fixture-pass'
    results['ws']=websocket(8888)
    results['wss']=websocket(8889,context)
    h2=ssl.create_default_context(cafile='/opt/wpt/tools/certs/cacert.pem');h2.set_alpn_protocols(['h2'])
    with socket.create_connection(('127.0.0.1',9000),timeout=2) as raw:
        with h2.wrap_socket(raw,server_hostname='web-platform.test') as conn:
            if conn.selected_alpn_protocol()!='h2':raise RuntimeError('H2 ALPN differs')
    results['h2']='tls-alpn-pass'
    return results

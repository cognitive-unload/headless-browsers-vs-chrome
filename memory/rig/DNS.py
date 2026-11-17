"""Container-loopback DNS only. No host DNS/network settings are changed."""
import ipaddress, json, os, socket, struct, threading, time
UPSTREAM=('1.1.1.1',53)

def answer(query):
    if len(query)<12 or struct.unpack('>H',query[4:6])[0]!=1: raise ValueError('single question required')
    pos=12; labels=[]
    while query[pos]:
        n=query[pos]
        if n>63:raise ValueError('compressed question not supported')
        pos+=1;labels.append(query[pos:pos+n].decode('ascii'));pos+=n
    pos+=1; typ,cls=struct.unpack('>HH',query[pos:pos+4]); question=query[12:pos+4]; name='.'.join(labels).lower().rstrip('.')
    if name=='telemetry.lightpanda.io' or name.endswith('.telemetry.lightpanda.io'):
        with open('/out/DNS.jsonl','a') as f:f.write(json.dumps({'time':time.time(),'name':name,'action':'blocked-nxdomain'})+'\n')
        return query[:2]+struct.pack('>HHHHH',0x8183,1,0,0,0)+question
    if name.endswith('.test'):
        bases=('web-platform.test','not-web-platform.test')
        subdomains={s.encode('idna').decode('ascii') for s in ('www','www1','www2','天気の良い日','élève')}
        base=next((b for b in bases if name==b or name.endswith('.'+b)),None)
        prefix=name[:-len(base)].rstrip('.').split('.') if base and name!=base else []
        valid=base is not None and len(prefix)<=2 and all(p in subdomains for p in prefix)
        if not valid:return query[:2]+struct.pack('>HHHHH',0x8183,1,0,0,0)+question
        data=ipaddress.ip_address('127.0.0.1').packed if typ==1 else None
        header=query[:2]+struct.pack('>HHHHH',0x8180,1,int(data is not None),0,0)
        return header+question+(b'\xc0\x0c'+struct.pack('>HHIH',typ,1,60,len(data))+data if data else b'')
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.settimeout(3);s.sendto(query,UPSTREAM);response,_=s.recvfrom(65535)
        if response[:2]!=query[:2]:raise ValueError('DNS transaction mismatch')
        return response

def udp(sock):
    while True:
        data,peer=sock.recvfrom(65535)
        try:sock.sendto(answer(data),peer)
        except Exception:pass

def exact(conn,n):
    out=b''
    while len(out)<n:
        part=conn.recv(n-len(out))
        if not part:raise EOFError()
        out+=part
    return out

def main():
    u=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);u.bind(('127.0.0.1',53))
    threading.Thread(target=udp,args=(u,),daemon=True).start()
    with socket.socket() as server:
        server.bind(('127.0.0.1',53));server.listen(8)
        while True:
            conn,_=server.accept()
            with conn:
                conn.settimeout(3)
                try:
                    n=struct.unpack('>H',exact(conn,2))[0];response=answer(exact(conn,n));conn.sendall(struct.pack('>H',len(response))+response)
                except Exception:pass
if __name__=='__main__':main()

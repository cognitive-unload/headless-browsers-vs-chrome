"""Obscura local fixtures opt in only inside a verified isolated namespace."""
import argparse,fcntl,pathlib,socket,struct

ENGINES=('chrome','lightpanda','obscura','moli')
PHASES=('preflight','wpt','sites','speed','benchmark')
LOCAL_PHASES=('preflight','wpt','benchmark')

def mode(engine,phase):
    if engine not in ENGINES or phase not in PHASES:
        raise ValueError('unknown engine/phase')
    return 'none' if engine=='obscura' and phase in LOCAL_PHASES else 'bridge'

def inspect_namespace():
    # if_nameindex enumerates interfaces, unlike sysfs (also has bonding_masters).
    ipv6={}
    for line in pathlib.Path('/proc/net/if_inet6').read_text().splitlines():
        fields=line.split();ipv6.setdefault(fields[-1],[]).append(fields[0])
    interfaces=[]
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        for index,name in socket.if_nameindex():
            request=struct.pack('256s',name.encode())
            flags=struct.unpack_from('H',fcntl.ioctl(sock.fileno(),0x8913,request),16)[0] # SIOCGIFFLAGS
            try:address=socket.inet_ntoa(fcntl.ioctl(sock.fileno(),0x8915,request)[20:24]) # SIOCGIFADDR
            except OSError as error:
                # Linux EADDRNOTAVAIL is the known unnumbered-interface result.
                if error.errno!=99:raise
                address=None
            interfaces.append(dict(name=name,index=index,flags=flags,ipv4=address,ipv6=ipv6.get(name,[])))
    v4=[line.split()[0] for line in pathlib.Path('/proc/net/route').read_text().splitlines()[1:] if line.strip()]
    v6=[line.split()[-1] for line in pathlib.Path('/proc/net/ipv6_route').read_text().splitlines() if line.strip()]
    caps={line.split(':',1)[0]:int(line.split(':',1)[1].strip(),16)
          for line in pathlib.Path('/proc/self/status').read_text().splitlines() if line.startswith('Cap')}
    return dict(interfaces=interfaces,ipv4_route_interfaces=v4,ipv6_route_interfaces=v6,capabilities=caps)

def require_isolated(namespace):
    interfaces={row['name']:row for row in namespace['interfaces']}
    if 'lo' not in interfaces or set(interfaces)-{'lo','tunl0'}:
        raise RuntimeError('unexpected interface in local-only namespace')
    if not interfaces['lo']['flags']&1:raise RuntimeError('loopback is down')
    for name,row in interfaces.items():
        if name!='lo' and (row['flags']&1 or row['ipv4'] or row['ipv6']):
            raise RuntimeError('non-loopback interface is up or addressed')
    if any(name!='lo' for name in namespace['ipv4_route_interfaces']+namespace['ipv6_route_interfaces']):
        raise RuntimeError('non-loopback route in local-only namespace')
    required={'CapInh','CapPrm','CapEff','CapBnd','CapAmb'}
    if set(namespace['capabilities'])!=required or any(namespace['capabilities'].values()):
        raise RuntimeError('local-only opt-in requires zero capability sets')

def configure(engine,phase,environment,namespace):
    result=dict(environment);result.pop('OBSCURA_ALLOW_PRIVATE_NETWORK',None)
    local=mode(engine,phase)=='none'
    if local:
        require_isolated(namespace)
        result['OBSCURA_ALLOW_PRIVATE_NETWORK']='1'
    receipt=dict(engine=engine,phase=phase,docker_network=mode(engine,phase),namespace=namespace,
                 private_network_opt_in=local,scope='local fixtures; loopback active; optional tunl0 down and unnumbered; no non-loopback routes or capabilities' if local else 'default engine SSRF policy')
    return result,receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('engine',choices=ENGINES);parser.add_argument('phase',choices=PHASES)
    args=parser.parse_args();print(mode(args.engine,args.phase))

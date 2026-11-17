"""Bounded 8-bit RGB/RGBA PNG decoder, pixel comparison, no third-party code."""
import struct, zlib

class UnsupportedPNG(ValueError): pass

def decode(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('PNG signature')
    p=8; data=bytearray(); header=None
    while p < len(raw):
        n=struct.unpack('>I',raw[p:p+4])[0]; kind=raw[p+4:p+8]; payload=raw[p+8:p+8+n]
        if zlib.crc32(kind+payload)&0xffffffff != struct.unpack('>I',raw[p+8+n:p+12+n])[0]:
            raise ValueError('PNG CRC')
        if kind==b'IHDR': header=struct.unpack('>IIBBBBB',payload)
        if kind==b'IDAT': data.extend(payload)
        p+=n+12
        if kind==b'IEND': break
    w,h,depth,color,compression,filter_method,interlace=header
    if depth!=8 or color not in (2,6) or interlace or w*h>1280*720:
        raise UnsupportedPNG(str(header))
    channels=3 if color==2 else 4; stride=w*channels
    dec=zlib.decompressobj(); packed=dec.decompress(bytes(data), (stride+1)*h+1)
    if len(packed)!=(stride+1)*h or not dec.eof: raise ValueError('PNG decoded size')
    rows=[]; previous=bytearray(stride); pos=0
    for y in range(h):
        f=packed[pos]; pos+=1; row=bytearray(packed[pos:pos+stride]); pos+=stride
        for i in range(stride):
            a=row[i-channels] if i>=channels else 0; b=previous[i]
            c=previous[i-channels] if i>=channels else 0
            if f==1: predictor=a
            elif f==2: predictor=b
            elif f==3: predictor=(a+b)//2
            elif f==4:
                q=a+b-c; distances=[abs(q-a),abs(q-b),abs(q-c)]
                predictor=[a,b,c][distances.index(min(distances))]
            elif f==0: predictor=0
            else: raise UnsupportedPNG('filter '+str(f))
            row[i]=(row[i]+predictor)&255
        previous=bytearray(row)
        if channels==3: row=bytearray(v for i in range(w) for v in (*row[i*3:i*3+3],255))
        rows.append(bytes(row))
    return w,h,b''.join(rows)

def compare(a,b):
    wa,ha,pa=decode(a); wb,hb,pb=decode(b)
    if (wa,ha)!=(wb,hb): raise ValueError('unequal image geometry')
    maximum=0; changed=0
    for i in range(0,len(pa),4):
        d=max(abs(pa[i+j]-pb[i+j]) for j in range(4))
        maximum=max(maximum,d); changed+=bool(d)
    return dict(maxDifference=maximum,totalPixels=changed)

def dimensions(raw):
    if raw[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('PNG signature')
    return struct.unpack('>II',raw[16:24])

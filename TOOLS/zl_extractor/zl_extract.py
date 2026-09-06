#!/usr/bin/env python3
"""Extract Zircon .Zl libraries to RGBA PNG while preserving original IDs."""
from __future__ import annotations
import argparse, io, json, struct, zlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

CODECS={0:'dxt1',1:'dxt5',2:'bgra32',3:'bc7',4:'png'}
PREFS={0:'none',1:'bgra32',2:'bc7_dxt5',3:'bc7',4:'dxt1',5:'dxt5',6:'source'}

class ZlError(RuntimeError): pass

def read(fmt,b,o):
    n=struct.calcsize(fmt)
    if o<0 or o+n>len(b): raise ZlError(f'truncated data at 0x{o:X} ({fmt})')
    return struct.unpack_from(fmt,b,o),o+n

def relkey(path,root):
    try: p=path.resolve().relative_to(root.resolve()) if root else Path(path.name)
    except ValueError: p=Path(path.name)
    return str(p.with_suffix('')).replace('\\','/')

@dataclass
class Img:
    id:int; present:bool; position:Optional[int]=None
    width:Optional[int]=None; height:Optional[int]=None
    offsetX:Optional[int]=None; offsetY:Optional[int]=None
    shadowType:Optional[int]=None; shadowWidth:Optional[int]=None; shadowHeight:Optional[int]=None
    shadowOffsetX:Optional[int]=None; shadowOffsetY:Optional[int]=None
    overlayWidth:Optional[int]=None; overlayHeight:Optional[int]=None
    imageCodec:Optional[str]=None; shadowCodec:Optional[str]=None; overlayCodec:Optional[str]=None
    imageRuntimePreference:Optional[str]=None; shadowRuntimePreference:Optional[str]=None; overlayRuntimePreference:Optional[str]=None
    storedImageDataSize:Optional[int]=None; imageBc7DataSize:Optional[int]=None; imageFallbackDataSize:Optional[int]=None
    storedShadowDataSize:Optional[int]=None; shadowBc7DataSize:Optional[int]=None; shadowFallbackDataSize:Optional[int]=None
    storedOverlayDataSize:Optional[int]=None; overlayBc7DataSize:Optional[int]=None; overlayFallbackDataSize:Optional[int]=None
    file:Optional[str]=None

@dataclass
class Entry:
    id:int; uncompressed:int; compressed:int; offset:int; compression:int; codec:int; type:int

@dataclass
class Lib:
    path:Path; key:str; format:str; version:int; slots:int; images:list[Img]; data:bytes
    entries:Optional[Dict[int,Entry]]=None

def parse(path:Path,root:Optional[Path]=None)->Lib:
    b=path.read_bytes(); key=relkey(path,root)
    return parse_zl2(path,key,b) if b.startswith(b'ZL2') else parse_legacy(path,key,b)

def legacy_meta(h,o,i,codec):
    v,o=read('<ihhhhBhhhhhh',h,o)
    pos,w,he,ox,oy,st,sw,sh,sox,soy,ow,oh=v
    return Img(i,True,pos,w,he,ox,oy,st,sw,sh,sox,soy,ow,oh,codec,codec,codec),o

def parse_legacy(path,key,b):
    if len(b)<8: raise ZlError(f'{path}: too small')
    (hs,),_=read('<i',b,0)
    if hs<4 or 4+hs>len(b): raise ZlError(f'{path}: invalid header size {hs}')
    h=b[4:4+hs]; (value,),o=read('<i',h,0)
    ver=(value>>25)&0x7f; count=(value&0x1ffffff) if ver else value
    if ver not in (0,1) or count<0: raise ZlError(f'{path}: unsupported legacy version/count {ver}/{count}')
    codec='dxt1' if ver==0 else 'dxt5'; images=[]
    for i in range(count):
        (p,),o=read('<B',h,o)
        if not p: images.append(Img(i,False)); continue
        m,o=legacy_meta(h,o,i,codec); images.append(m)
    if o!=len(h): raise ZlError(f'{path}: metadata mismatch {o}!={len(h)}')
    return Lib(path,key,'ZL_LEGACY',ver,count,images,b)

def parse_zl2(path,key,b):
    if len(b)<43: raise ZlError(f'{path}: truncated ZL2 header')
    o=3; (ver,count,_atlas),o=read('<iii',b,o); (_def,_flags,_r),o=read('<BBh',b,o)
    (mo,),o=read('<q',b,o); (ms,),o=read('<i',b,o); (ioff,),o=read('<q',b,o); (isz,),o=read('<i',b,o)
    if ver<2 or mo<0 or ms<0 or mo+ms>len(b) or ioff<0 or isz<0 or ioff+isz>len(b): raise ZlError(f'{path}: invalid ZL2 header')
    idx=b[ioff:ioff+isz]; (ec,),x=read('<i',idx,0); entries={}
    for _ in range(ec):
        (typ,),x=read('<B',idx,x); (eid,unc,comp),x=read('<iii',idx,x); (po,),x=read('<q',idx,x); (cm,co),x=read('<BB',idx,x)
        entries[eid]=Entry(eid,unc,comp,po,cm,co,typ)
    if x!=len(idx): raise ZlError(f'{path}: ZL2 index mismatch')
    m=b[mo:mo+ms]; x=0; (mver,mcount,_grp,_page),x=read('<iiii',m,x)
    if mcount!=count: raise ZlError(f'{path}: ZL2 image count mismatch')
    images=[]
    for i in range(count):
        (p,),x=read('<B',m,x)
        if not p: images.append(Img(i,False)); continue
        base,x=read('<ihhhhBhhhhhh',m,x)
        pos,w,he,ox,oy,st,sw,sh,sox,soy,ow,oh=base
        (_atlaspage,),x=read('<i',m,x); _,x=read('<hhhh',m,x); _,x=read('<hhhh',m,x)
        (ic,sc,oc,ip,sp,op),x=read('<BBBBBB',m,x); sizes,x=read('<iiiiiiiii',m,x)
        images.append(Img(i,True,pos,w,he,ox,oy,st,sw,sh,sox,soy,ow,oh,
            CODECS.get(ic,f'unknown_{ic}'),CODECS.get(sc,f'unknown_{sc}'),CODECS.get(oc,f'unknown_{oc}'),
            PREFS.get(ip,f'unknown_{ip}'),PREFS.get(sp,f'unknown_{sp}'),PREFS.get(op,f'unknown_{op}'),*sizes))
    return Lib(path,key,'ZL2',mver,count,images,b,entries)

def blocks(w,h,n): return 0 if w<=0 or h<=0 else ((w+3)//4)*((h+3)//4)*n

def dds(w,h,codec,n):
    four=b'DXT1' if codec=='dxt1' else b'DXT5'; flags=0x2100F; caps=0x1000
    q=struct.pack('<IIIII',124,flags,h,w,n)+struct.pack('<II',0,0)+struct.pack('<11I',*([0]*11))
    q+=struct.pack('<II',32,4)+four+struct.pack('<5I',0,0,0,0,0)+struct.pack('<I',caps)+struct.pack('<4I',0,0,0,0)
    return b'DDS '+q

def dds_bc7(w,h,n):
    flags=0x2100F; caps=0x1000
    q=struct.pack('<IIIII',124,flags,h,w,n)+struct.pack('<II',0,0)+struct.pack('<11I',*([0]*11))
    q+=struct.pack('<II',32,4)+b'DX10'+struct.pack('<5I',0,0,0,0,0)+struct.pack('<I',caps)+struct.pack('<4I',0,0,0,0)
    return b'DDS '+q+struct.pack('<IIIII',98,3,0,1,0)

def decode(payload,w,h,codec):
    if w<=0 or h<=0: raise ZlError(f'invalid size {w}x{h}')
    if codec=='png': return Image.open(io.BytesIO(payload)).convert('RGBA')
    if codec=='bgra32':
        n=w*h*4
        if len(payload)<n: raise ZlError('short BGRA32 payload')
        return Image.frombytes('RGBA',(w,h),payload[:n],'raw','BGRA')
    if codec in ('dxt1','dxt5'):
        n=blocks(w,h,8 if codec=='dxt1' else 16)
        if len(payload)<n: raise ZlError(f'short {codec} payload')
        return Image.open(io.BytesIO(dds(w,h,codec,n)+payload[:n])).convert('RGBA')
    if codec=='bc7':
        n=blocks(w,h,16)
        if len(payload)<n: raise ZlError('short bc7 payload')
        return Image.open(io.BytesIO(dds_bc7(w,h,n)+payload[:n])).convert('RGBA')
    raise ZlError(f'unsupported codec {codec}')

def inflate(p,kind,n):
    if kind==0: out=p
    elif kind in (1,2):
        try: out=zlib.decompress(p,-zlib.MAX_WBITS)
        except zlib.error: out=zlib.decompress(p)
    else: raise ZlError(f'unsupported ZL2 compression {kind}')
    if len(out)!=n: raise ZlError(f'payload size {len(out)}!={n}')
    return out

def image_payload(lib:Lib,m:Img):
    w=m.width or 0; h=m.height or 0
    if lib.format=='ZL_LEGACY':
        co=m.imageCodec or ('dxt1' if lib.version==0 else 'dxt5'); n=blocks(w,h,8 if co=='dxt1' else 16); p=m.position or 0
        if p<=0 or p+n>len(lib.data): raise ZlError(f'{lib.key}:{m.id} invalid position')
        return lib.data[p:p+n],co
    if m.position is None or m.position<0 or not lib.entries or m.position not in lib.entries: raise ZlError(f'{lib.key}:{m.id} missing ZL2 entry')
    e=lib.entries[m.position]; raw=lib.data[e.offset:e.offset+e.compressed]; pay=inflate(raw,e.compression,e.uncompressed)
    a=m.storedImageDataSize or 0; b=m.imageBc7DataSize or 0; c=m.imageFallbackDataSize or 0
    if a: return pay[:a],m.imageCodec or 'png'
    if b: return pay[a:a+b],'bc7'
    if c: return pay[a+b:a+b+c],'dxt5'
    raise ZlError(f'{lib.key}:{m.id} has no main payload')

def manifest(lib,source):
    return {'formatVersion':1,'key':lib.key,'sourceFile':source,'zlFormat':lib.format,'zlVersion':lib.version,
        'slotCount':lib.slots,'presentCount':sum(x.present for x in lib.images),'idPolicy':'original_zircon_id_preserved',
        'transparency':'encoded_alpha_preserved','images':[asdict(x) for x in lib.images]}

def extract(lib:Lib,out:Path,mroot:Path):
    d=out/Path(lib.key); d.mkdir(parents=True,exist_ok=True)
    for m in lib.images:
        if not m.present: continue
        p,co=image_payload(lib,m); im=decode(p,m.width or 0,m.height or 0,co)
        fn=f'{m.id:05d}.png'; im.convert('RGBA').save(d/fn,'PNG',compress_level=9); m.file=str(Path(lib.key)/fn).replace('\\','/')
    src=f'ZIRCON_ASSETS/originals/{lib.key}.Zl'; obj=manifest(lib,src); mp=mroot/(lib.key+'.json'); mp.parent.mkdir(parents=True,exist_ok=True); mp.write_text(json.dumps(obj,indent=2)+'\n')
    return obj

def collect(ps):
    out=[]
    for p in ps:
        if p.is_dir(): out+=sorted(x for x in p.rglob('*') if x.is_file() and x.suffix.lower()=='.zl')
        elif p.is_file(): out.append(p)
        else: raise FileNotFoundError(p)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('inputs',nargs='+',type=Path); ap.add_argument('--source-root',type=Path)
    ap.add_argument('--extracted-root',type=Path,default=Path('ZIRCON_ASSETS/extracted')); ap.add_argument('--manifests-root',type=Path,default=Path('ZIRCON_ASSETS/manifests')); ap.add_argument('--scan-only',action='store_true'); a=ap.parse_args()
    for p in collect(a.inputs):
        lib=parse(p,a.source_root); src=f'ZIRCON_ASSETS/originals/{lib.key}.Zl'
        if a.scan_only:
            obj=manifest(lib,src); obj['extractionStatus']='metadata_only'; mp=a.manifests_root/(lib.key+'.json'); mp.parent.mkdir(parents=True,exist_ok=True); mp.write_text(json.dumps(obj,indent=2)+'\n')
        else: obj=extract(lib,a.extracted_root,a.manifests_root)
        print(f"{lib.key}: {lib.format} v{lib.version}, slots={lib.slots}, present={obj['presentCount']}")
if __name__=='__main__': main()

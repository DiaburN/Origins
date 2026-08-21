#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

HEADER = 28
CELL = 14
SUPPORTED = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,15,19,25,255}

# Source coordinates are from the official Zircon Bichon Map/0.map (800x800).
# They are copied as native cells; no artwork is generated or inferred.
FLOOR = (306, 184, 12, 12)          # clean/passable Bichon grass field
TOP_CAVE = (300, 90, 60, 40)        # coherent Bichon Caves entrance + surroundings
LEFT_WALL = (290, 96, 10, 16)       # dense natural/forest edge
RIGHT_WALL = (350, 98, 10, 16)      # cliff/rock-heavy edge
CAVE_REGION_SOURCE = [(329,119),(330,119),(329,120),(330,120),(330,121),(330,122)]

TARGET_W = 80
TARGET_H = 128
TOP_X = 10
TOP_Y = 0
SIDE_W = 10
TOP_H = 40
BOTTOM_H = 16
SPAWN = (TARGET_W // 2, TARGET_H - BOTTOM_H - 8)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class NativeMap:
    def __init__(self, raw: bytes, label: str):
        self.raw = bytearray(raw)
        self.label = label
        if len(raw) < HEADER:
            raise ValueError(f"{label}: too short")
        self.w = struct.unpack_from('<H', raw, 22)[0]
        self.h = struct.unpack_from('<H', raw, 24)[0]
        self.back_base = HEADER
        self.cell_base = HEADER + (self.w // 2) * (self.h // 2) * 3
        expected = self.cell_base + self.w * self.h * CELL
        if len(raw) != expected:
            raise ValueError(f"{label}: {len(raw)} bytes, expected {expected} for {self.w}x{self.h}")

    def back_pos(self, x: int, y: int) -> int:
        if x % 2 or y % 2:
            raise ValueError('back coordinates must be even/even')
        bx, by = x // 2, y // 2
        return self.back_base + (bx * (self.h // 2) + by) * 3

    def cell_pos(self, x: int, y: int) -> int:
        return self.cell_base + (x * self.h + y) * CELL

    def back(self, x: int, y: int) -> bytes:
        p = self.back_pos(x,y)
        return bytes(self.raw[p:p+3])

    def cell(self, x: int, y: int) -> bytes:
        p = self.cell_pos(x,y)
        return bytes(self.raw[p:p+CELL])

    def ids(self, x: int, y: int) -> tuple[int,int]:
        p = self.cell_pos(x,y)
        return self.raw[p+4], self.raw[p+3]  # middle, front


class NewMap:
    def __init__(self, source: NativeMap, w: int, h: int):
        self.w, self.h = w, h
        size = HEADER + (w//2)*(h//2)*3 + w*h*CELL
        self.raw = bytearray(size)
        self.raw[:22] = source.raw[:22]
        struct.pack_into('<HH', self.raw, 22, w, h)
        self.raw[26:28] = source.raw[26:28]
        self.back_base = HEADER
        self.cell_base = HEADER + (w//2)*(h//2)*3

    def back_pos(self,x,y):
        return self.back_base + ((x//2)*(self.h//2)+(y//2))*3

    def cell_pos(self,x,y):
        return self.cell_base + (x*self.h+y)*CELL

    def set_back(self,x,y,payload: bytes):
        p=self.back_pos(x,y); self.raw[p:p+3]=payload

    def set_cell(self,x,y,payload: bytes):
        p=self.cell_pos(x,y); self.raw[p:p+CELL]=payload

    def set_passable(self,x,y,value: bool):
        p=self.cell_pos(x,y)
        if value: self.raw[p] |= 0x03
        else: self.raw[p] &= 0xFC

    def ids(self,x,y):
        p=self.cell_pos(x,y)
        return self.raw[p+4], self.raw[p+3]


def source_xy_for_floor(tx: int, ty: int) -> tuple[int,int]:
    x0,y0,pw,ph = FLOOR
    sx=x0+(tx%pw); sy=y0+(ty%ph)
    # Keep parity aligned so half-resolution Back tiles remain exact.
    if (sx & 1) != (tx & 1): sx = x0 + ((sx-x0+1)%pw)
    if (sy & 1) != (ty & 1): sy = y0 + ((sy-y0+1)%ph)
    return sx,sy


def initialise_authentic_floor(src: NativeMap, out: NewMap) -> None:
    for x in range(out.w):
        for y in range(out.h):
            sx,sy=source_xy_for_floor(x,y)
            payload=bytearray(src.cell(sx,sy))
            mf,ff=payload[4],payload[3]
            # The selected floor is almost entirely terrain-only. If a rare tall
            # object lands in the repeating sample, remove only that object cell;
            # Back and native Wood_Tilesc terrain layers remain untouched.
            if mf not in (0,15,255) or ff not in (0,15,255):
                payload[1]=0; payload[2]=0
                payload[3]=255; payload[4]=255
                struct.pack_into('<H',payload,5,0)
                struct.pack_into('<H',payload,7,0)
            payload[0] |= 0x03
            out.set_cell(x,y,payload)
            if x%2==0 and y%2==0:
                out.set_back(x,y,src.back(sx,sy))


def copy_patch(src: NativeMap, out: NewMap, sx: int, sy: int, pw: int, ph: int, tx: int, ty: int) -> None:
    if ((sx-tx)&1) or ((sy-ty)&1):
        raise ValueError('patch source/target parity must match')
    for dx in range(pw):
        for dy in range(ph):
            x,y=tx+dx,ty+dy
            if not (0<=x<out.w and 0<=y<out.h):
                continue
            out.set_cell(x,y,src.cell(sx+dx,sy+dy))
            if x%2==0 and y%2==0:
                out.set_back(x,y,src.back(sx+dx,sy+dy))


def build(src: NativeMap) -> tuple[NewMap,dict]:
    if (src.w,src.h)!=(800,800):
        raise ValueError(f'Expected official Bichon 0.map 800x800, got {src.w}x{src.h}')

    out=NewMap(src,TARGET_W,TARGET_H)
    initialise_authentic_floor(src,out)

    # Coherent top section: the actual Bichon Caves entrance, copied whole.
    copy_patch(src,out,*TOP_CAVE,TOP_X,TOP_Y)

    # Repeated native boundary strips. These are copied as complete 10x16 chunks
    # rather than assembling guessed ImageIDs, so their multi-cell art remains native.
    for y in range(TOP_H,TARGET_H-BOTTOM_H,16):
        ph=min(16,TARGET_H-BOTTOM_H-y)
        copy_patch(src,out,LEFT_WALL[0],LEFT_WALL[1],SIDE_WALL_W:=LEFT_WALL[2],ph,0,y)
        copy_patch(src,out,RIGHT_WALL[0],RIGHT_WALL[1],RIGHT_WALL[2],ph,TARGET_W-SIDE_WALL_W,y)

    # Fill the two top corners beside the 60-cell cave patch.
    for y in range(0,TOP_H,16):
        ph=min(16,TOP_H-y)
        copy_patch(src,out,LEFT_WALL[0],LEFT_WALL[1],LEFT_WALL[2],ph,0,y)
        copy_patch(src,out,RIGHT_WALL[0],RIGHT_WALL[1],RIGHT_WALL[2],ph,TARGET_W-SIDE_WALL_W,y)

    # F1 has NO rear door. Build a solid natural bottom boundary from the same
    # authentic forest/rock chunks, alternating them across the width.
    y0=TARGET_H-BOTTOM_H
    for x in range(0,TARGET_W,10):
        patch=LEFT_WALL if (x//10)%2==0 else RIGHT_WALL
        copy_patch(src,out,patch[0],patch[1],10,BOTTOM_H,x,y0)

    # Perimeter collision is explicit regardless of the source chunk collision.
    for x in range(TARGET_W):
        for y in range(TARGET_H):
            if x<SIDE_W or x>=TARGET_W-SIDE_W or y>=TARGET_H-BOTTOM_H:
                out.set_passable(x,y,False)

    # The cave's real Bichon movement region is remapped exactly into the top patch.
    cave=[]
    for sx,sy in CAVE_REGION_SOURCE:
        tx=TOP_X+(sx-TOP_CAVE[0]); ty=TOP_Y+(sy-TOP_CAVE[1])
        cave.append((tx,ty)); out.set_passable(tx,ty,True)

    # Ensure the central fight space and spawn are walkable without altering art.
    for x in range(SIDE_W,TARGET_W-SIDE_W):
        for y in range(TOP_H,TARGET_H-BOTTOM_H):
            out.set_passable(x,y,True)

    used=Counter()
    for x in range(TARGET_W):
        for y in range(TARGET_H):
            if x%2==0 and y%2==0:
                p=out.back_pos(x,y); used[out.raw[p]]+=1
            p=out.cell_pos(x,y)
            for fid in (out.raw[p+4],out.raw[p+3]):
                if fid not in (0,255): used[fid]+=1
    unknown=sorted(k for k in used if k not in SUPPORTED)
    if unknown:
        raise ValueError(f'Unsupported KROrder ids in generated room: {unknown}')

    report={
        'schema':'origins.forest-room.v1',
        'source':{'map':'official Zircon Map/0.map','width':src.w,'height':src.h,'sha256':sha(src.raw)},
        'output':{'width':TARGET_W,'height':TARGET_H,'spawn':SPAWN},
        'sourcePatches':{
            'floor':FLOOR,'topCave':TOP_CAVE,'leftForestEdge':LEFT_WALL,'rightRockEdge':RIGHT_WALL,
        },
        'caveSourceRegion':CAVE_REGION_SOURCE,
        'caveTargetRegion':cave,
        'usedKROrderIds':sorted(used),
        'usedCounts':dict(sorted(used.items())),
        'contract':[
            'All visible cells originate from official Zircon Bichon 0.map.',
            'No PNG artwork, procedural fake tile, or invented ImageID is used.',
            'F1 has no rear/bottom door.',
            'Central room is wide/open and intended for clear-all-monsters progression.',
            'Upper cave entrance is the real Bichon Caves entrance patch.',
        ],
    }
    return out,report


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-map',type=Path,required=True)
    ap.add_argument('--output-map',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    a=ap.parse_args()
    src=NativeMap(a.source_map.read_bytes(),a.source_map.name)
    out,report=build(src)
    a.output_map.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.output_map.write_bytes(out.raw)
    report['output']['bytes']=len(out.raw)
    report['output']['sha256']=sha(out.raw)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

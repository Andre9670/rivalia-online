"""Walkability RIGOROSA: block=4, un nodo è walkable SOLO se il 100% dei suoi pixel è pavimento
(zero muri/acqua/lava dentro). Questo garantisce che l'A* non tagli dentro i muri.
Diagonali: gestite a runtime col no-corner-cutting. Output: walk-grid-rigorous.json + transitions (riuso)."""
from PIL import Image
import json

WALK = {(0,204,0),(0,102,0),(0,255,0),(255,204,153),(102,102,102),(153,153,153),(153,102,51),
        (255,255,255),(51,51,51),(153,51,0),(255,102,0),(255,255,0)}  # giallo incluso (transizione calpestabile)
NFLOORS=16; BLOCK=4
def load(fl): return Image.open(f'minimap/floor-{fl}.png').convert('RGB')
ims=[load(f) for f in range(NFLOORS)]
W,H=ims[0].size
GW=(W+BLOCK-1)//BLOCK; GH=(H+BLOCK-1)//BLOCK

def build(fl):
    px=ims[fl].load(); rows=[]
    for by in range(GH):
        row=[]
        for bx in range(GW):
            allwalk=True
            for y in range(by*BLOCK,min((by+1)*BLOCK,H)):
                for x in range(bx*BLOCK,min((bx+1)*BLOCK,W)):
                    if px[x,y] not in WALK: allwalk=False;break
                if not allwalk: break
            row.append(1 if allwalk else 0)
        rows.append(row)
    return rows

grids=[build(fl) for fl in range(NFLOORS)]
def comps_stat(g):
    seen=set(); comps=[]
    for y in range(GH):
        for x in range(GW):
            if g[y][x]==1 and (x,y) not in seen:
                st=[(x,y)];seen.add((x,y));sz=0
                while st:
                    cx,cy=st.pop();sz+=1
                    for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        if 0<=cx+dx<GW and 0<=cy+dy<GH and g[cy+dy][cx+dx]==1 and (cx+dx,cy+dy) not in seen:
                            seen.add((cx+dx,cy+dy));st.append((cx+dx,cy+dy))
                comps.append(sz)
    comps.sort(reverse=True); tot=sum(comps)
    return tot,len(comps),(100*comps[0]//tot if tot else 0),comps[:5]
for fl in (6,7,8):
    tot,nc,lp,t5=comps_stat(grids[fl])
    print(f"floor{fl}: walkable={tot} comps={nc} largest={lp}% top5={t5}")

out={'block':BLOCK,'gw':GW,'gh':GH,'w':W,'h':H,'floors':[[''.join(map(str,r)) for r in g] for g in grids]}
json.dump(out,open('walk-grid-rigorous.json','w'))
import os; print("walk-grid-rigorous.json:",os.path.getsize('walk-grid-rigorous.json')//1024,"KB")

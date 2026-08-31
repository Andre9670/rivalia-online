"""FASE 0 — estrae walkability + transizioni cross-piano dalle minimap.
Transizione = pixel giallo (255,255,0) clusterizzato in punto discreto, VALIDATO se il piano
adiacente (sopra=indice-1 / sotto=indice+1) è calpestabile nello stesso punto.
Output: transitions.json + walk-grid ridotta (blocchi) per il pathfinding."""
from PIL import Image
import json, collections

WALK = {(0,204,0),(0,102,0),(255,204,153),(102,102,102),(153,153,153),(153,102,51),
        (255,255,255),(51,51,51),(153,51,0),(255,102,0)}
YELLOW=(255,255,0)
NFLOORS=16
BLOCK=8   # griglia ridotta: 8x8 px -> 1 nodo pathfinding

def load(fl): return Image.open(f'minimap/floor-{fl}.png').convert('RGB')
ims=[load(f) for f in range(NFLOORS)]
W,H=ims[0].size
PX=[im.load() for im in ims]

def is_walk(fl,x,y):
    if fl<0 or fl>=NFLOORS or x<0 or y<0 or x>=W or y>=H: return False
    return PX[fl][x,y] in WALK

# --- connected-components clustering del giallo per piano (8-connect) ---
def yellow_components(fl):
    px=PX[fl]; seen=[[False]*W for _ in range(H)] if False else None
    visited=set(); comps=[]
    # raccogli gialli
    ys={}
    for y in range(H):
        for x in range(W):
            if px[x,y]==YELLOW: ys[(x,y)]=True
    for (sx,sy) in list(ys.keys()):
        if (sx,sy) in visited: continue
        # BFS
        stack=[(sx,sy)]; comp=[]
        visited.add((sx,sy))
        while stack:
            x,y=stack.pop(); comp.append((x,y))
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    nx,ny=x+dx,y+dy
                    if (nx,ny) in ys and (nx,ny) not in visited:
                        visited.add((nx,ny)); stack.append((nx,ny))
        # centroide
        cx=sum(p[0] for p in comp)//len(comp); cy=sum(p[1] for p in comp)//len(comp)
        comps.append((cx,cy,len(comp)))
    return comps

transitions=[]
per_floor={}
for fl in range(NFLOORS):
    comps=yellow_components(fl)
    cnt=0
    for cx,cy,size in comps:
        if size<2: continue   # scarta pixel isolato singolo (rumore)
        up = any(is_walk(fl-1,cx+dx,cy+dy) for dx in(-2,-1,0,1,2) for dy in(-2,-1,0,1,2))
        dn = any(is_walk(fl+1,cx+dx,cy+dy) for dx in(-2,-1,0,1,2) for dy in(-2,-1,0,1,2))
        typ='both' if (up and dn) else ('up' if up else ('down' if dn else None))
        if not typ: continue
        transitions.append({'x':cx,'y':cy,'floor':fl,'type':typ,'size':size})
        cnt+=1
    per_floor[fl]=cnt

json.dump(transitions, open('transitions.json','w'))
print("TOTAL transitions:", len(transitions))
print("per floor:", per_floor)

"""Griglia ridotta di walkability: blocchi 8x8 px -> 1 nodo. Un nodo è walkable se >=25%
dei suoi pixel sono pavimento. Output compatto: per piano, righe RLE di bit."""
from PIL import Image
import json

WALK = {(0,204,0),(0,102,0),(255,204,153),(102,102,102),(153,153,153),(153,102,51),
        (255,255,255),(51,51,51),(153,51,0),(255,102,0)}
YELLOW=(255,255,0)
NFLOORS=16; BLOCK=8
def load(fl): return Image.open(f'minimap/floor-{fl}.png').convert('RGB')
ims=[load(f) for f in range(NFLOORS)]
W,H=ims[0].size
GW=(W+BLOCK-1)//BLOCK; GH=(H+BLOCK-1)//BLOCK
print("grid:",GW,"x",GH,"=",GW*GH,"nodes/floor")

grids=[]
for fl in range(NFLOORS):
    px=ims[fl].load()
    rows=[]
    for by in range(GH):
        row=[]
        for bx in range(GW):
            wc=0; tot=0
            for y in range(by*BLOCK, min((by+1)*BLOCK,H)):
                for x in range(bx*BLOCK, min((bx+1)*BLOCK,W)):
                    tot+=1
                    if px[x,y] in WALK or px[x,y]==YELLOW: wc+=1
            row.append(1 if tot and wc/tot>=0.25 else 0)
        rows.append(row)
    grids.append(rows)
    if fl in (6,7,8):
        wsum=sum(sum(r) for r in rows)
        print(f"floor{fl}: walkable nodes={wsum}/{GW*GH}")

# compatta: per piano una stringa di '0'/'1' per riga, joinate — semplice e comprimibile
out={'block':BLOCK,'gw':GW,'gh':GH,'w':W,'h':H,
     'floors':[[''.join(map(str,r)) for r in g] for g in grids]}
json.dump(out, open('walk-grid.json','w'))
import os
print("walk-grid.json:", os.path.getsize('walk-grid.json')//1024,"KB")

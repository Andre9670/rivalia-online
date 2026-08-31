"""Pathdata a risoluzione piena: block=1 (1 nodo = 1 tile). Esatto e sicuro (nessuna aggregazione)."""
from PIL import Image
import json,os
WALK={(0,204,0),(0,102,0),(0,255,0),(255,204,153),(102,102,102),(153,153,153),(153,102,51),
      (255,255,255),(51,51,51),(153,51,0),(255,102,0),(255,255,0),(255,51,0)}
YELLOW=(255,255,0); NF=16
ims=[Image.open(f'minimap/floor-{f}.png').convert('RGB') for f in range(NF)]
W,H=ims[0].size; PX=[im.load() for im in ims]
def rle_row(fl,y):
    px=PX[fl];out=[];cur=0;run=0
    for x in range(W):
        b=1 if px[x,y] in WALK else 0
        if b==cur:run+=1
        else:out.append(run);cur=b;run=1
    out.append(run);return out
grid={'block':1,'gw':W,'gh':H,'w':W,'h':H,'floors':[[rle_row(fl,y) for y in range(H)] for fl in range(NF)]}
json.dump(grid,open('pathdata-grid.json','w'),separators=(',',':'))
# transizioni a block=1: il centroide giallo È già il tile
def is_walk(fl,x,y): return 0<=fl<NF and 0<=x<W and 0<=y<H and PX[fl][x,y] in WALK
def yellow_comps(fl):
    px=PX[fl];ys=set((x,y) for y in range(H) for x in range(W) if px[x,y]==YELLOW)
    vis=set();comps=[]
    for s in list(ys):
        if s in vis:continue
        st=[s];vis.add(s);c=[]
        while st:
            x,y=st.pop();c.append((x,y))
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    n=(x+dx,y+dy)
                    if n in ys and n not in vis:vis.add(n);st.append(n)
        cx=sum(p[0] for p in c)//len(c);cy=sum(p[1] for p in c)//len(c)
        comps.append((cx,cy,len(c)))
    return comps
trans=[]
for fl in range(NF):
    for cx,cy,size in yellow_comps(fl):
        if size<2:continue
        up=any(is_walk(fl-1,cx+dx,cy+dy) for dx in(-2,-1,0,1,2) for dy in(-2,-1,0,1,2))
        dn=any(is_walk(fl+1,cx+dx,cy+dy) for dx in(-2,-1,0,1,2) for dy in(-2,-1,0,1,2))
        typ='both' if(up and dn) else('up' if up else('down' if dn else None))
        if not typ:continue
        trans.append([cx,cy,fl,{'up':0,'down':1,'both':2}[typ]])
json.dump(trans,open('pathdata-trans.json','w'),separators=(',',':'))
print("grid:",os.path.getsize('pathdata-grid.json')//1024,"KB | transitions:",len(trans),os.path.getsize('pathdata-trans.json')//1024,"KB")

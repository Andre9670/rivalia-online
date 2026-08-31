"""Genera gli asset di pathfinding definitivi: walk-grid RLE (block=4, 100% walkable) + transitions.
Eseguito una volta; build_html.py li inlina."""
from PIL import Image
import json,os
# Walkable colors. NOTE on the greys (Andrea's ground-truth, verified on z7+z11):
#  - (153,153,153) light grey = stone floor (Thais streets, dungeons) → WALKABLE
#  - (102,102,102) dark grey  = ALWAYS non-walkable (mountains on surface, rock/walls underground).
#    It's the same RGB for cave-floor artifacts, but treating it as wall matches the game everywhere.
WALK_BASE={(0,204,0),(0,102,0),(0,255,0),(255,204,153),(153,153,153),(153,102,51),
      (255,255,255),(51,51,51),(153,51,0),(255,102,0),(255,255,0)}
def is_walk_col(fl,col):
    return col in WALK_BASE   # (102,102,102) dark grey deliberately excluded on ALL floors
YELLOW=(255,255,0); NF=16; B=1   # block=1 → 1 minimap pixel = 1 game tile (no downsampling; avoids false walls)
ims=[Image.open(f'minimap/floor-{f}.png').convert('RGB') for f in range(NF)]
W,H=ims[0].size; GW=(W+B-1)//B; GH=(H+B-1)//B; PX=[im.load() for im in ims]
def is_walk_px(fl,x,y): return 0<=fl<NF and 0<=x<W and 0<=y<H and is_walk_col(fl,PX[fl][x,y])
def build(fl):
    px=PX[fl];rows=[]
    for y in range(H):
        row=[('1' if is_walk_col(fl,px[x,y]) else '0') for x in range(W)]
        rows.append(''.join(row))
    return rows
grids=[build(fl) for fl in range(NF)]
def rle(s):
    out=[];cur='0';run=0
    for ch in s:
        if ch==cur:run+=1
        else:out.append(run);cur=ch;run=1
    out.append(run);return out
grid_rle={'block':B,'gw':GW,'gh':GH,'w':W,'h':H,'floors':[[rle(r) for r in g] for g in grids]}
json.dump(grid_rle,open('pathdata-grid.json','w'),separators=(',',':'))

# transizioni: connected components giallo, size>=2, validate su piano adiacente walkable (+-2px block)
def yellow_comps(fl):
    px=PX[fl];ys=set()
    for y in range(H):
        for x in range(W):
            if px[x,y]==YELLOW: ys.add((x,y))
    visited=set();comps=[]
    for s in list(ys):
        if s in visited:continue
        st=[s];visited.add(s);c=[]
        while st:
            x,y=st.pop();c.append((x,y))
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    n=(x+dx,y+dy)
                    if n in ys and n not in visited:visited.add(n);st.append(n)
        cx=sum(p[0] for p in c)//len(c);cy=sum(p[1] for p in c)//len(c)
        comps.append((cx,cy,len(c)))
    return comps
def gblock_walk(fl,gx,gy):
    if fl<0 or fl>=NF or gx<0 or gy<0 or gx>=GW or gy>=GH:return False
    return grids[fl][gy][gx]=='1'
# precompute a per-floor set of yellow-marker blocks (for the yellow<->yellow rule)
yellow_blocks=[set() for _ in range(NF)]
for fl in range(NF):
    for cx,cy,size in yellow_comps(fl):
        if size>=2: yellow_blocks[fl].add((cx//B,cy//B))
def gblock_yellow(fl,gx,gy):
    if fl<0 or fl>=NF:return False
    return (gx,gy) in yellow_blocks[fl]
trans=[]; recovered=0
for fl in range(NF):
    for cx,cy,size in yellow_comps(fl):
        if size<2:continue
        gx=cx//B;gy=cy//B
        # a transition is valid if the ADJACENT floor is walkable at the landing point (original rule)
        # OR it also has an aligned yellow marker (Andrea's insight: two aligned dots = a passage,
        #   e.g. shovel/rope holes whose landing tile isn't painted walkable on the minimap)
        up_w=any(gblock_walk(fl-1,gx+dx,gy+dy) for dx in(-1,0,1) for dy in(-1,0,1))
        dn_w=any(gblock_walk(fl+1,gx+dx,gy+dy) for dx in(-1,0,1) for dy in(-1,0,1))
        up_y=any(gblock_yellow(fl-1,gx+dx,gy+dy) for dx in(-1,0,1) for dy in(-1,0,1))
        dn_y=any(gblock_yellow(fl+1,gx+dx,gy+dy) for dx in(-1,0,1) for dy in(-1,0,1))
        up=up_w or up_y; dn=dn_w or dn_y
        typ='both' if(up and dn) else('up' if up else('down' if dn else None))
        if not typ:continue
        if (up and not up_w) or (dn and not dn_w): recovered+=1
        trans.append([gx,gy,fl,{'up':0,'down':1,'both':2}[typ]])  # compact: [gx,gy,floor,typecode]
json.dump(trans,open('pathdata-trans.json','w'),separators=(',',':'))
print("grid:",os.path.getsize('pathdata-grid.json')//1024,"KB | transitions:",len(trans),
      f"({recovered} via yellow<->yellow)", os.path.getsize('pathdata-trans.json')//1024,"KB")

from PIL import Image
import json
WALK = {(0,204,0),(0,102,0),(0,255,0),(255,204,153),(102,102,102),(153,153,153),(153,102,51),
        (255,255,255),(51,51,51),(153,51,0),(255,102,0),(255,255,0)}
NFLOORS=16
def load(fl): return Image.open(f'minimap/floor-{fl}.png').convert('RGB')
ims=[load(f) for f in range(NFLOORS)]; W,H=ims[0].size

def run(BLOCK,thr):
    GW=(W+BLOCK-1)//BLOCK; GH=(H+BLOCK-1)//BLOCK
    def build(fl):
        px=ims[fl].load(); rows=[]
        for by in range(GH):
            row=[]
            for bx in range(GW):
                wc=tot=0
                for y in range(by*BLOCK,min((by+1)*BLOCK,H)):
                    for x in range(bx*BLOCK,min((bx+1)*BLOCK,W)):
                        tot+=1
                        if px[x,y] in WALK: wc+=1
                row.append(1 if tot and wc/tot>=thr else 0)
            rows.append(row)
        return rows,GW,GH
    g,GW,GH=build(7)
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
    return tot,len(comps),(100*comps[0]//tot if tot else 0),comps[:3]

for BLOCK,thr in [(2,1.0),(2,0.9),(4,0.9),(4,0.75)]:
    tot,nc,lp,t3=run(BLOCK,thr)
    print(f"block={BLOCK} thr={thr}: fl7 walkable={tot} comps={nc} largest={lp}% top3={t3}")

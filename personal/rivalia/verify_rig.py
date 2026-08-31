"""Test locale: A* su walk-grid-rigorous (block=4, 100% walkable), no-corner-cutting sulle diagonali.
Verifica che i percorsi NON tocchino pixel muro/acqua/lava."""
import json,heapq,random
from PIL import Image
WG=json.load(open('walk-grid-rigorous.json'))
B=WG['block'];GW=WG['gw'];GH=WG['gh'];NF=len(WG['floors'])
G=WG['floors']
def walk(fl,x,y): return 0<=fl<NF and 0<=x<GW and 0<=y<GH and G[fl][y][x]=='1'
T=json.load(open('transitions.json'))
trans={}
for t in T:
    gx=t['x']//B;gy=t['y']//B;fl=t['floor'];k=(fl,gx,gy)
    if t['type'] in('up','both'):trans.setdefault(k,[]).append((fl-1))
    if t['type'] in('down','both'):trans.setdefault(k,[]).append((fl+1))
def neigh(n):
    fl,x,y=n
    for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        nx,ny=x+dx,y+dy
        if walk(fl,nx,ny):
            # no corner cutting: per diagonale, entrambi gli ortogonali adiacenti devono essere walkable
            if dx and dy and not(walk(fl,x+dx,y) and walk(fl,x,y+dy)):continue
            yield (fl,nx,ny),(1.4 if dx and dy else 1.0)
    for toFl in trans.get(n,[]):
        if walk(toFl,x,y): yield (toFl,x,y),3.0
def astar(s,g,cap=120000):
    def h(n):return abs(n[1]-g[1])+abs(n[2]-g[2])+abs(n[0]-g[0])*10
    pq=[(h(s),0,s)];came={};gs={s:0};e=0
    while pq:
        f,gc,n=heapq.heappop(pq)
        if n==g:
            p=[n]
            while n in came:n=came[n];p.append(n)
            return p[::-1],e
        e+=1
        if e>cap:return None,e
        for nb,c in neigh(n):
            ng=gc+c
            if nb not in gs or ng<gs[nb]:
                gs[nb]=ng;came[nb]=n;heapq.heappush(pq,(ng+h(nb),ng,nb))
    return None,e
# reachable set dal nodo più connesso di floor7
def big_comp(fl):
    best=None;seen=set()
    for y in range(GH):
        for x in range(GW):
            if walk(fl,x,y) and (x,y) not in seen:
                st=[(x,y)];seen.add((x,y));c=[(x,y)]
                while st:
                    cx,cy=st.pop()
                    for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        if walk(fl,cx+dx,cy+dy) and (cx+dx,cy+dy) not in seen:
                            seen.add((cx+dx,cy+dy));st.append((cx+dx,cy+dy));c.append((cx+dx,cy+dy))
                if not best or len(c)>len(best):best=c
    return best
comp=big_comp(7)
random.seed(3)
# pixel-check: carico minimap floor per verificare muri sotto ogni step
ims={fl:Image.open(f'minimap/floor-{fl}.png').convert('RGB').load() for fl in (6,7,8)}
WALLC={(51,0,204),(204,255,255),(51,255,255),(255,51,0)} # muro,acqua,ice,lava
def block_has_barrier(fl,gx,gy):
    px=ims.get(fl)
    if not px:return False
    for yy in range(gy*B,min((gy+1)*B,WG['h'])):
        for xx in range(gx*B,min((gx+1)*B,WG['w'])):
            if px[xx,yy] in WALLC:return True
    return False
solved=0;tot=0;barrier_steps=0;total_steps=0
for i in range(15):
    s=random.choice(comp);g=random.choice(comp)
    S=(7,s[0],s[1]);Gg=(7,g[0],g[1]);tot+=1
    p,e=astar(S,Gg)
    if p:
        solved+=1
        for (fl,x,y) in p:
            total_steps+=1
            if block_has_barrier(fl,x,y):barrier_steps+=1
print(f"same-comp reachable: solved {solved}/{tot}")
print(f"steps total={total_steps} | steps whose block contains ANY barrier pixel={barrier_steps} ({100*barrier_steps//max(1,total_steps)}%)")

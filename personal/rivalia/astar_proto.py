"""Prototipo A* cross-piano su walk-grid + transitions. Serve a VALIDARE il grafo prima del port JS."""
import json, heapq, math, sys

WG=json.load(open('walk-grid.json'))
BLOCK=WG['block']; GW=WG['gw']; GH=WG['gh']; NF=len(WG['floors'])
G=[[row for row in fl] for fl in WG['floors']]  # G[fl][gy] = string of '0'/'1'
def walk(fl,gx,gy):
    if fl<0 or fl>=NF or gx<0 or gy<0 or gx>=GW or gy>=GH: return False
    return G[fl][gy][gx]=='1'

# transizioni -> per nodo-blocco: dict (fl,gx,gy) -> list of (toFl, type)
T=json.load(open('transitions.json'))
trans={}
for t in T:
    gx=t['x']//BLOCK; gy=t['y']//BLOCK; fl=t['floor']
    key=(fl,gx,gy)
    if t['type'] in ('up','both'):   trans.setdefault(key,[]).append((fl-1,'up'))
    if t['type'] in ('down','both'): trans.setdefault(key,[]).append((fl+1,'down'))

def neighbors(n):
    fl,gx,gy=n
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        nx,ny=gx+dx,gy+dy
        if walk(fl,nx,ny):
            cost=1.0 if dx==0 or dy==0 else 1.4
            yield (fl,nx,ny),cost,None
    # transizioni: cambia piano se il nodo di arrivo è walkable
    for (toFl,typ) in trans.get(n,[]):
        if walk(toFl,gx,gy):
            yield (toFl,gx,gy),3.0,typ   # costo extra per cambio piano

def astar(start,goal,maxexp=200000):
    def h(n): return abs(n[1]-goal[1])+abs(n[2]-goal[2])+abs(n[0]-goal[0])*10
    openq=[(h(start),0,start,None)]; came={}; g={start:0}; exp=0
    while openq:
        f,gc,n,how=heapq.heappop(openq)
        if n==goal:
            # ricostruisci
            path=[]; cur=n
            while cur in came:
                path.append((cur,came[cur][1])); cur=came[cur][0]
            path.append((start,None)); path.reverse(); return path,exp
        exp+=1
        if exp>maxexp: return None,exp
        for nb,cost,typ in neighbors(n):
            ng=gc+cost
            if nb not in g or ng<g[nb]:
                g[nb]=ng; came[nb]=(n,typ); heapq.heappush(openq,(ng+h(nb),ng,nb,typ))
    return None,exp

def nearest_walk(fl,gx,gy,rad=40):
    best=None;bd=1e9
    for dx in range(-rad,rad):
        for dy in range(-rad,rad):
            if walk(fl,gx+dx,gy+dy):
                d=dx*dx+dy*dy
                if d<bd: bd=d;best=(fl,gx+dx,gy+dy)
    return best

if __name__=='__main__':
    # test: due punti sul piano 7, e uno cross-piano 7->6
    import random
    def rnd_walk(fl):
        for _ in range(5000):
            gx=random.randint(0,GW-1); gy=random.randint(0,GH-1)
            if walk(fl,gx,gy): return (fl,gx,gy)
        return None
    random.seed(1)
    ok=0; tot=0; changes=0
    for i in range(8):
        s=rnd_walk(7); ggoal=rnd_walk(random.choice([6,7,8]))
        if not s or not ggoal: continue
        tot+=1
        path,exp=astar(s,ggoal)
        if path:
            ok+=1
            fc=len(set(p[0][0] for p in path))
            changes+=sum(1 for p in path if p[1])
            print(f"route {i}: {s}->{ggoal} | path len={len(path)} floors={fc} transitions_used={sum(1 for p in path if p[1])} exp={exp}")
        else:
            print(f"route {i}: {s}->{ggoal} | NO PATH exp={exp}")
    print(f"\nSOLVED {ok}/{tot}")

import json
from collections import defaultdict
data=json.load(open('hunt-spots.json'))
sample={'amazon','valkyrie','witch','cyclops','cyclops-warrior','minotaur-guard','ghoul'}

def build(data,cre):
    pts=[]
    for name,sp in data.items():
        if name not in cre: continue
        for s in sp: pts.append((name,s['x'],s['y'],s['z']))
    return pts

class UF:
    def __init__(s,n): s.p=list(range(n))
    def f(s,a):
        while s.p[a]!=a: s.p[a]=s.p[s.p[a]]; a=s.p[a]
        return a
    def u(s,a,b): s.p[s.f(a)]=s.f(b)

def band(z):
    return 'surface' if z<7 else ('ground' if z==7 else 'under')

def cluster(pts,dist,zmode):
    # zmode: 'adj'(|dz|<=1), 'exact'(dz==0), 'band'(same band)
    n=len(pts); uf=UF(n)
    grid=defaultdict(list)
    for i,(nm,x,y,z) in enumerate(pts):
        key=(x//dist,y//dist, z if zmode!='band' else band(z))
        grid[key].append(i)
    keys=list(grid)
    for (gx,gy,gz),idxs in grid.items():
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                zr=[gz] if zmode=='band' else [gz+d for d in (-1,0,1)]
                for gz2 in zr:
                    k=(gx+dx,gy+dy,gz2)
                    if k not in grid: continue
                    for i in idxs:
                        for j in grid[k]:
                            if j<=i: continue
                            _,xi,yi,zi=pts[i]; _,xj,yj,zj=pts[j]
                            if abs(xi-xj)<=dist and abs(yi-yj)<=dist:
                                if zmode=='exact' and zi!=zj: continue
                                if zmode=='adj' and abs(zi-zj)>1: continue
                                if zmode=='band' and band(zi)!=band(zj): continue
                                uf.u(i,j)
    cl=defaultdict(list)
    for i in range(n): cl[uf.f(i)].append(i)
    return list(cl.values())

def report(pts,groups,title,topn=12):
    out=[]
    for g in groups:
        cps=[pts[i] for i in g]
        xs=[p[1] for p in cps]; ys=[p[2] for p in cps]; zs=sorted(set(p[3] for p in cps))
        cre=defaultdict(int)
        for p in cps: cre[p[0]]+=1
        out.append((len(cps),round(sum(xs)/len(xs)),round(sum(ys)/len(ys)),min(zs),max(zs),dict(sorted(cre.items(),key=lambda k:-k[1]))))
    out.sort(key=lambda c:-c[0])
    big=out[0][0]
    print(f"\n=== {title}: {len(out)} clusters, biggest={big} pts ===")
    for n,cx,cy,zmn,zmx,cre in out[:topn]:
        print(f"  x~{cx} y~{cy} fl{zmn}-{zmx} | {n}pts | "+', '.join(f'{k}({v})' for k,v in cre.items()))

pts=build(data,sample)
for dist in (150,100,60):
    g=cluster(pts,dist,'adj')
    report(pts,g,f"dist={dist} adjacent-floor")
g=cluster(pts,100,'exact'); report(pts,g,"dist=100 EXACT-floor")
g=cluster(pts,150,'band'); report(pts,g,"dist=150 BAND(surf/ground/under)")

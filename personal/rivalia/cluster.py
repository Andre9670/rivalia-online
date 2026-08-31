import json, sys
from collections import defaultdict

DIST = 150      # max x/y distance to be in same zone
DZ   = 1        # adjacent-floor tolerance

def load():
    return json.load(open('hunt-spots.json'))

def build_points(data, creatures=None):
    pts = []
    for name, spawns in data.items():
        if creatures is not None and name not in creatures:
            continue
        for s in spawns:
            pts.append({'creature':name,'x':s['x'],'y':s['y'],'z':s['z'],
                        'amount':s.get('amount',1),'radius':s.get('radius'),'time':s.get('time')})
    return pts

class UF:
    def __init__(s,n): s.p=list(range(n))
    def find(s,a):
        while s.p[a]!=a: s.p[a]=s.p[s.p[a]]; a=s.p[a]
        return a
    def union(s,a,b): s.p[s.find(a)]=s.find(b)

def cluster(pts):
    n=len(pts)
    uf=UF(n)
    # spatial grid bucket by (x//DIST, y//DIST, z) to limit pair checks
    grid=defaultdict(list)
    for i,p in enumerate(pts):
        grid[(p['x']//DIST, p['y']//DIST, p['z'])].append(i)
    for (gx,gy,gz),idxs in grid.items():
        # check neighbours within +-1 cell on x,y and +-DZ on z
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for dz in range(-DZ,DZ+1):
                    key=(gx+dx,gy+dy,gz+dz)
                    if key not in grid: continue
                    for i in idxs:
                        for j in grid[key]:
                            if j<=i: continue
                            pi,pj=pts[i],pts[j]
                            if abs(pi['x']-pj['x'])<=DIST and abs(pi['y']-pj['y'])<=DIST and abs(pi['z']-pj['z'])<=DZ:
                                uf.union(i,j)
    clusters=defaultdict(list)
    for i in range(n): clusters[uf.find(i)].append(i)
    return list(clusters.values())

def summarize(pts, groups):
    out=[]
    for g in groups:
        cps=[pts[i] for i in g]
        xs=[p['x'] for p in cps]; ys=[p['y'] for p in cps]; zs=sorted(set(p['z'] for p in cps))
        cx=round(sum(xs)/len(xs)); cy=round(sum(ys)/len(ys))
        cre=defaultdict(int)
        for p in cps: cre[p['creature']]+=1
        out.append({'cx':cx,'cy':cy,'zmin':min(zs),'zmax':max(zs),'zs':zs,
                    'npts':len(cps),'creatures':dict(sorted(cre.items(),key=lambda kv:-kv[1]))})
    out.sort(key=lambda c:-c['npts'])
    return out

if __name__=='__main__':
    data=load()
    sample=['amazon','valkyrie','witch','cyclops','cyclops-warrior','minotaur-guard','ghoul']
    pts=build_points(data,set(sample))
    groups=cluster(pts)
    summ=summarize(pts,groups)
    print(f"Total sample points: {len(pts)}  ->  {len(summ)} clusters\n")
    for i,c in enumerate(summ,1):
        crs=', '.join(f"{k}({v})" for k,v in c['creatures'].items())
        print(f"Z{i:02d}  x~{c['cx']} y~{c['cy']}  floor {c['zmin']}-{c['zmax']}  | {c['npts']} pts | {crs}")

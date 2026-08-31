import json, csv
from collections import defaultdict
DIST=60; DZ=1
data=json.load(open('hunt-spots.json'))

pts=[]
for name,sp in data.items():
    for s in sp:
        pts.append({'creature':name,'x':s['x'],'y':s['y'],'z':s['z'],
                    'amount':s.get('amount',1),'radius':s.get('radius'),'time':s.get('time')})

class UF:
    def __init__(s,n): s.p=list(range(n))
    def f(s,a):
        while s.p[a]!=a: s.p[a]=s.p[s.p[a]]; a=s.p[a]
        return a
    def u(s,a,b): s.p[s.f(a)]=s.f(b)

n=len(pts); uf=UF(n)
grid=defaultdict(list)
for i,p in enumerate(pts): grid[(p['x']//DIST,p['y']//DIST,p['z'])].append(i)
for (gx,gy,gz),idxs in grid.items():
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            for dz in range(-DZ,DZ+1):
                k=(gx+dx,gy+dy,gz+dz)
                if k not in grid: continue
                for i in idxs:
                    pi=pts[i]
                    for j in grid[k]:
                        if j<=i: continue
                        pj=pts[j]
                        if abs(pi['x']-pj['x'])<=DIST and abs(pi['y']-pj['y'])<=DIST and abs(pi['z']-pj['z'])<=DZ:
                            uf.u(i,j)
cl=defaultdict(list)
for i in range(n): cl[uf.f(i)].append(i)

clusters=[]
for g in cl.values():
    cps=[pts[i] for i in g]
    xs=[p['x'] for p in cps]; ys=[p['y'] for p in cps]; zs=sorted(set(p['z'] for p in cps))
    cre=defaultdict(lambda:{'spawn_points':0,'total_amount':0})
    for p in cps:
        cre[p['creature']]['spawn_points']+=1
        cre[p['creature']]['total_amount']+=p['amount']
    clusters.append({'cx':round(sum(xs)/len(xs)),'cy':round(sum(ys)/len(ys)),
        'floor_min':min(zs),'floor_max':max(zs),'floors':zs,
        'spawn_points':len(cps),
        'creatures':dict(sorted(cre.items(),key=lambda kv:-kv[1]['spawn_points']))})
# sort by density (spawn_points) desc, then geographically
clusters.sort(key=lambda c:(-c['spawn_points'],c['cx'],c['cy']))
for i,c in enumerate(clusters,1): c['zone_id']=f"Z{i:03d}"
c0=clusters[0]
# build label
for c in clusters:
    c['label']=f"{c['zone_id']} — x~{c['cx']} y~{c['cy']} floor {c['floor_min']}-{c['floor_max']}"

# JSON out
out={'meta':{'source':'https://wiki.rivaliaonline.com/hunt-spots.json',
    'generated_for':'Rivalia Online (custom Tibia 7.4)',
    'clustering':{'method':'single-linkage union-find','xy_radius':DIST,'floor_tolerance':DZ,
        'note':'Zones are coordinate-based clusters; Rivalia has no published city/zone names so labels are raw coordinates.'},
    'creatures_total':len(data),'spawn_points_total':n,'zones_total':len(clusters)},
    'zones':clusters}
json.dump(out,open('rivalia-zones.json','w'),indent=2)

# CSV out: one row per zone x creature
with open('rivalia-zones.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['zone_id','x_centro','y_centro','floor_min','floor_max','creatura','num_spawn','total_amount'])
    for c in clusters:
        for cre,v in c['creatures'].items():
            w.writerow([c['zone_id'],c['cx'],c['cy'],c['floor_min'],c['floor_max'],cre,v['spawn_points'],v['total_amount']])

# stats
sizes=[c['spawn_points'] for c in clusters]
singletons=sum(1 for s in sizes if s==1)
print(f"All 174 creatures | {n} spawn points -> {len(clusters)} zones (radius {DIST}, adj floor)")
print(f"Biggest zone: {max(sizes)} pts | singletons (1 pt): {singletons} | zones with >=10 pts: {sum(1 for s in sizes if s>=10)}")
print(f"\nTop 25 zones by density:")
for c in clusters[:25]:
    crs=', '.join(f"{k}({v['spawn_points']})" for k,v in list(c['creatures'].items())[:6])
    more='' if len(c['creatures'])<=6 else f" +{len(c['creatures'])-6}more"
    print(f"  {c['zone_id']} x~{c['cx']} y~{c['cy']} fl{c['floor_min']}-{c['floor_max']} |{c['spawn_points']:4d}p| {crs}{more}")

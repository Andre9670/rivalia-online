import json
from collections import defaultdict
data=json.load(open('hunt-spots.json'))
pts=[]
for name,sp in data.items():
    for s in sp: pts.append((name,s['x'],s['y'],s['z'],s.get('amount',1)))

def band(z): return 0 if z<7 else (1 if z==7 else 2)  # surface/ground/under
BANDNAME={0:'surface(<7)',1:'ground(7)',2:'under(>7)'}

def gridcluster(pts,G,zmode):
    # zmode 'band' or 'exact'
    cells=defaultdict(list)
    for p in pts:
        nm,x,y,z,a=p
        zk= band(z) if zmode=='band' else z
        cells[(x//G,y//G,zk)].append(p)
    return cells

for G in (200,150,250):
    for zmode in ('band','exact'):
        cells=gridcluster(pts,G,zmode)
        sizes=sorted((len(v) for v in cells.values()),reverse=True)
        big=sizes[0]; n10=sum(1 for s in sizes if s>=10); sing่=sum(1 for s in sizes if s==1)
        print(f"G={G} z={zmode:5s} -> {len(cells)} zones | biggest={big} | >=10pts:{n10} | singletons:{sing if (sing:=sum(1 for s in sizes if s==1)) else 0}")

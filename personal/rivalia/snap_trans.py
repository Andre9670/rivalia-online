"""Aggancia ogni transizione al tile walkable più vicino sul piano di ORIGINE (entro ±2),
così l'A* può sempre raggiungerla. La destinazione la aggancia l'A* a runtime."""
import json
grid=json.load(open('pathdata-grid.json')); W=grid['w'];H=grid['h'];NF=len(grid['floors'])
T=json.load(open('pathdata-trans.json'))
cache={}
def rb(fl,y):
    runs=grid['floors'][fl][y];bits=bytearray(W);x=0;cur=0
    for r in runs:
        if cur:
            for k in range(r):
                if x+k<W:bits[x+k]=1
        x+=r;cur^=1
    return bits
def walk(fl,x,y):
    if fl<0 or fl>=NF or y<0 or y>=H or x<0 or x>=W:return False
    key=(fl,y)
    if key not in cache:cache[key]=rb(fl,y)
    return cache[key][x]==1
out=[];snapped=dropped=0
for cx,cy,fl,tc in T:
    if walk(fl,cx,cy):
        out.append([cx,cy,fl,tc]); continue
    # cerca walkable più vicino su origine
    best=None;bd=99
    for dx in range(-2,3):
        for dy in range(-2,3):
            if walk(fl,cx+dx,cy+dy):
                d=dx*dx+dy*dy
                if d<bd:bd=d;best=(cx+dx,cy+dy)
    if best: out.append([best[0],best[1],fl,tc]); snapped+=1
    else: dropped+=1
json.dump(out,open('pathdata-trans.json','w'),separators=(',',':'))
print(f"transizioni: {len(out)} (snapped su origine: {snapped}, droppate senza walkable: {dropped})")

import json, csv
from collections import defaultdict
G=150
data=json.load(open('hunt-spots.json'))
def band(z): return 'surface' if z<7 else ('ground' if z==7 else 'under')

cells=defaultdict(list)
for name,sp in data.items():
    for s in sp:
        x,y,z=s['x'],s['y'],s['z']
        cells[(x//G,y//G,band(z))].append({'creature':name,'x':x,'y':y,'z':z,'amount':s.get('amount',1)})

zones=[]
for (gx,gy,bnd),cps in cells.items():
    xs=[p['x'] for p in cps]; ys=[p['y'] for p in cps]; zs=sorted(set(p['z'] for p in cps))
    cre=defaultdict(lambda:{'spawn_points':0,'total_amount':0})
    for p in cps:
        cre[p['creature']]['spawn_points']+=1
        cre[p['creature']]['total_amount']+=p['amount']
    zones.append({'band':bnd,'cx':round(sum(xs)/len(xs)),'cy':round(sum(ys)/len(ys)),
        'x_min':gx*G,'x_max':gx*G+G,'y_min':gy*G,'y_max':gy*G+G,
        'floor_min':min(zs),'floor_max':max(zs),'floors':zs,'spawn_points':len(cps),
        'creatures':dict(sorted(cre.items(),key=lambda kv:-kv[1]['spawn_points']))})
zones.sort(key=lambda c:(-c['spawn_points'],c['cx'],c['cy']))
for i,z in enumerate(zones,1):
    z['zone_id']=f"Z{i:03d}"
    z['label']=f"{z['zone_id']} — x~{z['cx']} y~{z['cy']} floor {z['floor_min']}-{z['floor_max']} ({z['band']})"

json.dump({'meta':{'source':'https://wiki.rivaliaonline.com/hunt-spots.json',
    'generated_for':'Rivalia Online (custom Tibia 7.4)',
    'clustering':{'method':'fixed-grid partition (non-chaining)','tile_size':G,
        'floor_grouping':'band: surface(<7)/ground(7)/under(>7)',
        'note':'Fixed tiles chosen because the map is a continuous dense spawn carpet on which proximity-chaining merges everything. Rivalia publishes no city/zone names (verified on /hunt/ page) so labels are raw coordinate tiles.'},
    'creatures_total':len(data),'spawn_points_total':sum(len(v) for v in cells.values()),
    'zones_total':len(zones)},'zones':zones},open('rivalia-zones.json','w'),indent=2)

with open('rivalia-zones.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['zone_id','x_centro','y_centro','x_min','x_max','y_min','y_max','band','floor_min','floor_max','creatura','num_spawn','total_amount'])
    for z in zones:
        for cre,v in z['creatures'].items():
            w.writerow([z['zone_id'],z['cx'],z['cy'],z['x_min'],z['x_max'],z['y_min'],z['y_max'],z['band'],z['floor_min'],z['floor_max'],cre,v['spawn_points'],v['total_amount']])

# --- sample verification: which zones do the 7 sample creatures appear in ---
sample=['amazon','valkyrie','witch','cyclops','cyclops-warrior','minotaur-guard','ghoul']
print("=== SAMPLE CHECK: zones where each sample creature appears (top zone per creature) ===")
for s in sample:
    hits=[(z['creatures'][s]['spawn_points'],z) for z in zones if s in z['creatures']]
    hits.sort(reverse=True,key=lambda h:h[0])
    tot=sum(h[0] for h in hits)
    top=hits[0][1]
    print(f"{s:16s} in {len(hits):2d} zones, {tot} pts | top: {top['zone_id']} x~{top['cx']} y~{top['cy']} fl{top['floor_min']}-{top['floor_max']} ({top['band']}) [{hits[0][0]}pts here]")

print(f"\n=== {len(zones)} zones total. Top 20 by density ===")
for z in zones[:20]:
    crs=', '.join(f"{k}({v['spawn_points']})" for k,v in list(z['creatures'].items())[:6])
    more='' if len(z['creatures'])<=6 else f" +{len(z['creatures'])-6}"
    print(f"{z['zone_id']} x~{z['cx']} y~{z['cy']} fl{z['floor_min']}-{z['floor_max']:2d} {z['band']:7s}|{z['spawn_points']:4d}p| {crs}{more}")

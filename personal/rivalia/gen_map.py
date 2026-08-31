import json
d=json.load(open('hunt-spots.json'))
OX,OY=31744,30701   # site origin: px = x-OX, py = y-OY
IMGW,IMGH=1685,2827

names=sorted(d.keys())
idx={n:i for i,n in enumerate(names)}

# per-floor points: [creatureIdx, px, py, amount, radius, time]
byfloor={z:[] for z in range(16)}
counts={}  # creature -> total
floorcount={z:0 for z in range(16)}
crByFloor={}  # name -> {floor:count}
for n,sp in d.items():
    counts[n]=0
    crByFloor[n]={}
    for s in sp:
        z=s['z']; px=s['x']-OX; py=s['y']-OY
        byfloor[z].append([idx[n],px,py,s.get('amount',1),s.get('radius',0),s.get('time',0)])
        counts[n]+=1; floorcount[z]+=1
        crByFloor[n][z]=crByFloor[n].get(z,0)+1

display={n:n.replace('-',' ').title() for n in names}

data={
  'names':names,
  'display':[display[n] for n in names],
  'total':[counts[n] for n in names],
  'crFloors':[sorted(crByFloor[n].keys()) for n in names],
  'byfloor':{str(z):byfloor[z] for z in range(16)},
  'floorcount':floorcount,
  'imgw':IMGW,'imgh':IMGH,
  'creaturesTotal':len(names),
  'spawnsTotal':sum(counts.values()),
}
json.dump(data,open('map-data.json','w'),separators=(',',':'))
print("data written. creatures",len(names),"spawns",data['spawnsTotal'])
print("floors with spawns:",{z:c for z,c in floorcount.items() if c})

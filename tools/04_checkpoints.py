# -*- coding: utf-8 -*-
"""店やスポットを見る前に、理想的なチェックポイント位置を先に置く。
   帯ごとに周回して等間隔に配り、実際の徒歩ネットワーク上の節点に吸着させる。"""
import json, math, os, heapq
from collections import defaultdict
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
SPEED=80.0; BANDS=[7,14,21,28,35]; ARC=760.0      # 帯に沿って置く間隔(m)
SEC=["N","NE","E","SE","S","SW","W","NW"]; SECJA={"N":"北","NE":"北東","E":"東","SE":"南東","S":"南","SW":"南西","W":"西","NW":"北西"}

core=json.load(open(os.path.join(D,'core.json'),encoding='utf-8'))
cy=sum(p[0] for p in core['polygon'])/len(core['polygon'])
cx=sum(p[1] for p in core['polygon'])/len(core['polygon'])
print(f'コアの重心 {cy:.5f},{cx:.5f}  面積 {core["area_km2"]}km²')

net=json.load(open(os.path.join(D,'walk_network.json'),encoding='utf-8'))
lat={};lon={}
for e in net['elements']:
    if e['type']=='node': lat[e['id']]=e['lat']; lon[e['id']]=e['lon']
adj=defaultdict(list)
def seg(a,b):
    t=math.pi/180; la1,lo1=lat[a],lon[a]; la2,lo2=lat[b],lon[b]
    return math.hypot((la2-la1)*t*6371000,(lo2-lo1)*t*6371000*math.cos((la1+la2)/2*t))
for e in net['elements']:
    if e['type']!='way': continue
    ns=[n for n in e.get('nodes',[]) if n in lat]
    for a,b in zip(ns,ns[1:]):
        if a!=b:
            d=seg(a,b); adj[a].append((b,d)); adj[b].append((a,d))
iso=json.load(open(os.path.join(D,'iso_nodes.json')))
tmin={}
for la,lo,mn in iso['nodes']: tmin[(round(la,6),round(lo,6))]=mn
nid={}
for n in adj:
    k=(round(lat[n],6),round(lon[n],6))
    if k in tmin: nid[n]=tmin[k]
print(f'時間つき節点 {len(nid):,}')

def hav(a1,o1,a2,o2):
    t=math.pi/180
    return 6371000*math.acos(max(-1,min(1,math.sin(a1*t)*math.sin(a2*t)+math.cos(a1*t)*math.cos(a2*t)*math.cos((o1-o2)*t))))
def brg(a1,o1,a2,o2):
    t=math.pi/180
    y=math.sin((o2-o1)*t)*math.cos(a2*t)
    x=math.cos(a1*t)*math.sin(a2*t)-math.sin(a1*t)*math.cos(a2*t)*math.cos((o2-o1)*t)
    return (math.atan2(y,x)/t+360)%360

cps=[]; cid=0
for b in BANDS:
    ring=[n for n,v in nid.items() if abs(v-b)<=0.9]
    ring.sort(key=lambda n: brg(cy,cx,lat[n],lon[n]))
    placed=[]
    for n in ring:
        p=(lat[n],lon[n])
        if any(hav(p[0],p[1],q[0],q[1])<ARC for q in placed): continue
        placed.append(p)
        bb=brg(cy,cx,p[0],p[1]); s=SEC[round(bb/45)%8]
        cid+=1
        cps.append({'checkpoint_id':f'CP{cid:03d}','band':b,'lat':round(p[0],6),'lon':round(p[1],6),
                    'bearing':round(bb,1),'sector':s,'sector_ja':SECJA[s],
                    'walk_min_from_core':round(nid[n],1),
                    'straight_from_core_m':round(hav(cy,cx,p[0],p[1]))})
    print(f'  {b:>2}分帯  周回の候補節点 {len(ring):>6,}  → 仮チェックポイント {len(placed):>3}')
print(f'仮チェックポイント 合計 {len(cps)}')

# 15±7分で行き来できる相手が何個あるか（実際の道で測る）
node_of={}
for c in cps:
    best=None; bd=1e9
    for n in adj:
        d=hav(c['lat'],c['lon'],lat[n],lon[n])
        if d<bd: bd=d; best=n
    node_of[c['checkpoint_id']]=best
LO,HI=8*SPEED,22*SPEED
for c in cps:
    s=node_of[c['checkpoint_id']]
    dist={s:0.0}; pq=[(0.0,s)]
    while pq:
        d,n=heapq.heappop(pq)
        if d>dist.get(n,1e18) or d>HI: continue
        for m,w in adj[n]:
            nd=d+w
            if nd<dist.get(m,1e18) and nd<=HI: dist[m]=nd; heapq.heappush(pq,(nd,m))
    reach=0
    for o in cps:
        if o is c: continue
        n=node_of[o['checkpoint_id']]
        if n in dist and LO<=dist[n]<=HI: reach+=1
    c['neighbours_15min']=reach
bad=[c for c in cps if c['neighbours_15min']<3]
print(f'15±7分の道のりで3つ以上つながる: {len(cps)-len(bad)}/{len(cps)}  （足りない {len(bad)}）')
from collections import Counter
print('  方位別:', dict(Counter(c['sector'] for c in cps)))
json.dump({'core_centroid':[round(cy,6),round(cx,6)],'arc_spacing_m':ARC,'checkpoints':cps},
          open(os.path.join(D,'checkpoints.json'),'w'), ensure_ascii=False)
print('→ data/checkpoints.json')

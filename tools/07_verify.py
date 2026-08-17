# -*- coding: utf-8 -*-
"""最終スポットで、実際の道のり15±7分の連鎖が成立するかを確かめる。"""
import json, math, os, heapq, random
from collections import defaultdict, Counter
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
SPEED=80.0; LO,HI=8*SPEED,22*SPEED
a=json.load(open(os.path.join(D,'assigned.json'),encoding='utf-8'))
cps=[c for c in a['checkpoints'] if c.get('spot_name')]
net=json.load(open(os.path.join(D,'walk_network.json'),encoding='utf-8'))
lat={};lon={}
for e in net['elements']:
    if e['type']=='node': lat[e['id']]=e['lat']; lon[e['id']]=e['lon']
adj=defaultdict(list)
def seg(p,q):
    t=math.pi/180
    return math.hypot((lat[q]-lat[p])*t*6371000,(lon[q]-lon[p])*t*6371000*math.cos((lat[p]+lat[q])/2*t))
for e in net['elements']:
    if e['type']!='way': continue
    ns=[n for n in e.get('nodes',[]) if n in lat]
    for p,q in zip(ns,ns[1:]):
        if p!=q: d=seg(p,q); adj[p].append((q,d)); adj[q].append((p,d))
def hav(a1,o1,a2,o2):
    t=math.pi/180
    return 6371000*math.acos(max(-1,min(1,math.sin(a1*t)*math.sin(a2*t)+math.cos(a1*t)*math.cos(a2*t)*math.cos((o1-o2)*t))))
# 孤立した枝道に吸着すると、そこから先へ辿れない。最大連結成分だけを使う。
seenc=set(); giant=set()
for st in adj:
    if st in seenc: continue
    comp=[]; stack=[st]; seenc.add(st)
    while stack:
        n=stack.pop(); comp.append(n)
        for m,_ in adj[n]:
            if m not in seenc: seenc.add(m); stack.append(m)
    if len(comp)>len(giant): giant=set(comp)
print(f'最大連結成分 {len(giant):,} / {len(adj):,} 節点')
node={}
for c in cps:
    b=None;bd=1e9
    for n in giant:
        d=hav(c['spot_lat'],c['spot_lon'],lat[n],lon[n])
        if d<bd: bd=d;b=n
    node[c['checkpoint_id']]=b
    if bd>120: print(f"   {c['checkpoint_id']} は道から {bd:.0f}m 離れている（{c['spot_name']}）")
E=defaultdict(list)
for c in cps:
    s=node[c['checkpoint_id']]; dist={s:0.0}; pq=[(0.0,s)]
    while pq:
        d,n=heapq.heappop(pq)
        if d>dist.get(n,1e18) or d>HI: continue
        for m,w in adj[n]:
            nd=d+w
            if nd<dist.get(m,1e18) and nd<=HI: dist[m]=nd; heapq.heappush(pq,(nd,m))
    for o in cps:
        if o is c: continue
        n=node[o['checkpoint_id']]
        if n in dist and LO<=dist[n]<=HI:
            E[c['checkpoint_id']].append((o['checkpoint_id'], round(dist[n]/SPEED,1)))
deg=[len(E[c['checkpoint_id']]) for c in cps]
print(f'隣接（実際の道で15±7分） 最小{min(deg)} 中央{sorted(deg)[len(deg)//2]} 最大{max(deg)}')
print(f'  3つ以上つながる: {sum(1 for d in deg if d>=3)}/{len(cps)}')
# 外向きの3連鎖が組めるか
byid={c['checkpoint_id']:c for c in cps}
random.seed(1); ok=0; ends=[]
for _ in range(2000):
    start=random.choice([c for c in cps if c['band']<=14])
    cur=start; used={cur['checkpoint_id']}; good=True
    for h in range(2):
        nxt=[byid[i] for i,_ in E[cur['checkpoint_id']]
             if i not in used and byid[i]['band']>cur['band']]
        if len(nxt)<3: good=False; break
        cur=random.choice(nxt); used.add(cur['checkpoint_id'])
    if good: ok+=1; ends.append(cur['band'])
print(f'内側から外へ3地点つなぐ: {100*ok/2000:.0f}% 成立   終点の帯 {dict(Counter(ends))}')
json.dump({cid:v for cid,v in E.items()}, open(os.path.join(D,'edges.json'),'w'))
for c in cps: c['neighbours_final']=len(E[c['checkpoint_id']])
json.dump(a, open(os.path.join(D,'assigned.json'),'w'), ensure_ascii=False)
print('→ data/edges.json')

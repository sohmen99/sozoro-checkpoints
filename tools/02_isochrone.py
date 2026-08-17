# -*- coding: utf-8 -*-
"""混雑コアの外周から、実際の徒歩ネットワークで 7/14/21/28/35 分の等時線を作る。
   直線の同心円ではなく道路グラフ上の距離なので、川・線路・大きな施設は自然に迂回する。"""
import json, math, heapq, os, array
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
SPEED=80.0            # m/分。アプリ本体と同じ
BANDS=[7,14,21,28,35]

core=json.load(open(os.path.join(D,'core.json'),encoding='utf-8'))
g=core['grid']; mask=[[c=='1' for c in row] for row in core['mask']]
def in_core(la,lo):
    y=int((la-g['lat0'])/g['dlat']); x=int((lo-g['lon0'])/g['dlon'])
    return 0<=y<g['ny'] and 0<=x<g['nx'] and mask[y][x]

net=json.load(open(os.path.join(D,'walk_network.json'),encoding='utf-8'))
lat={}; lon={}
for e in net['elements']:
    if e['type']=='node': lat[e['id']]=e['lat']; lon[e['id']]=e['lon']
adj={}
def hav(a,b):
    t=math.pi/180
    la1,lo1=lat[a],lon[a]; la2,lo2=lat[b],lon[b]
    dla=(la2-la1)*t; dlo=(lo2-lo1)*t; m=(la1+la2)/2*t
    return math.hypot(dla*6371000, dlo*6371000*math.cos(m))
edges=0
for e in net['elements']:
    if e['type']!='way': continue
    ns=[n for n in e.get('nodes',[]) if n in lat]
    for a,b in zip(ns,ns[1:]):
        if a==b: continue
        d=hav(a,b)
        adj.setdefault(a,[]).append((b,d)); adj.setdefault(b,[]).append((a,d)); edges+=1
print(f'グラフ  節点 {len(adj):,}  辺 {edges:,}')

src=[n for n in adj if in_core(lat[n],lon[n])]
print(f'コアの中にある節点 {len(src):,}（ここを起点0分とする）')

INF=float('inf'); dist={}; pq=[]
for n in src: dist[n]=0.0; heapq.heappush(pq,(0.0,n))
while pq:
    d,n=heapq.heappop(pq)
    if d>dist.get(n,INF): continue
    if d> (BANDS[-1]+6)*SPEED: continue          # 41分ぶんで打ち切り
    for m,w in adj[n]:
        nd=d+w
        if nd<dist.get(m,INF): dist[m]=nd; heapq.heappush(pq,(nd,m))
print(f'到達した節点 {len(dist):,}')

mins={n:dist[n]/SPEED for n in dist}
for b in BANDS:
    print(f'   {b:>2}分以内の節点 {sum(1 for v in mins.values() if v<=b):>7,}')

json.dump({'speed':SPEED,'bands':BANDS,
           'nodes':[[round(lat[n],6),round(lon[n],6),round(mins[n],2)] for n in mins]},
          open(os.path.join(D,'iso_nodes.json'),'w'))
print('→ data/iso_nodes.json')

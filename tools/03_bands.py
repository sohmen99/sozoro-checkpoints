# -*- coding: utf-8 -*-
"""等時線の節点を面に起こす。40mグリッドに落として輪郭を取り出す。
   節点の無いところ（川・線路の内側・大きな敷地）は到達不能として残る。"""
import json, math, os
from collections import defaultdict
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
iso=json.load(open(os.path.join(D,'iso_nodes.json')))
BANDS=iso['bands']; NODES=iso['nodes']
STEP=40.0
lats=[n[0] for n in NODES]; lons=[n[1] for n in NODES]
LAT0,LAT1=min(lats)-0.002,max(lats)+0.002
LON0,LON1=min(lons)-0.002,max(lons)+0.002
dlat=STEP/110570.0; dlon=STEP/(111320.0*math.cos(35.72*math.pi/180))
ny=int((LAT1-LAT0)/dlat)+1; nx=int((LON1-LON0)/dlon)+1
print(f'グリッド {nx} x {ny}')
INF=float('inf')
grid=[[INF]*nx for _ in range(ny)]
for la,lo,mn in NODES:
    y=int((la-LAT0)/dlat); x=int((lo-LON0)/dlon)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            b,a=y+dy,x+dx
            if 0<=b<ny and 0<=a<nx and mn<grid[b][a]: grid[b][a]=mn
reach=sum(1 for r in grid for v in r if v<INF)
print(f'到達セル {reach:,} / {nx*ny:,}  = {reach*STEP*STEP/1e6:.1f} km²')

def contour(thr):
    def inside(y,x): return 0<=y<ny and 0<=x<nx and grid[y][x]<=thr
    segs=[]
    for y in range(-1,ny):
        for x in range(-1,nx):
            a,b,c,d=inside(y,x),inside(y,x+1),inside(y+1,x+1),inside(y+1,x)
            pts={'N':(y+1,x+0.5),'S':(y,x+0.5),'W':(y+0.5,x),'E':(y+0.5,x+1)}
            code=(a<<3)|(b<<2)|(c<<1)|d
            tbl={1:[('W','N')],2:[('N','E')],3:[('W','E')],4:[('S','E')],5:[('W','N'),('S','E')],
                 6:[('N','S')],7:[('W','S')],8:[('W','S')],9:[('N','S')],10:[('W','S'),('N','E')],
                 11:[('S','E')],12:[('W','E')],13:[('N','E')],14:[('W','N')]}
            for p,q in tbl.get(code,[]): segs.append((pts[p],pts[q]))
    adj=defaultdict(list)
    for p,q in segs: adj[p].append(q); adj[q].append(p)
    rings=[]; seen=set()
    for st in list(adj):
        if st in seen: continue
        ring=[st]; seen.add(st); cur, prev = st, None
        while True:
            nx2=[v for v in adj[cur] if v!=prev and v not in seen]
            if not nx2: break
            prev, cur = cur, nx2[0]; seen.add(cur); ring.append(cur)
        if len(ring)>=20: rings.append(ring)
    rings.sort(key=len, reverse=True)
    out=[]
    for r in rings[:6]:
        pts=[[round(LAT0+p[0]*dlat,6), round(LON0+p[1]*dlon,6)] for p in r[::2]]
        if len(pts)>=10: out.append(pts)
    return out

bands={}
for b in BANDS:
    rings=contour(b)
    bands[str(b)]=rings
    print(f'  {b:>2}分  輪郭 {len(rings)} 本 / 最大 {max((len(r) for r in rings), default=0)} 点')
json.dump({'bands':BANDS,'rings':bands}, open(os.path.join(D,'bands.json'),'w'))
print('→ data/bands.json')

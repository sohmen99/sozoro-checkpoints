# -*- coding: utf-8 -*-
"""混雑コア領域を面として決める。

1kmメッシュの人流データはこの縮尺を解けない（上野公園の値が周辺の中央値より
低く出る）ので、輪郭は主要混雑地点からの面で起こし、メッシュは検証に使う。
"""
import json, math, os
G = os.path.dirname(os.path.abspath(__file__))
APP = '/Users/shimizukento/Documents/ハッカソン/index.html'
s = open(APP, encoding='utf-8').read()
i = s.index('var OD_MESH = '); j = s.index('\n', i)
MESH = json.loads(s[i + len('var OD_MESH = '):s.rindex(';', i, j)])

# 混雑の核。上野駅一点にせず、実際に人が溜まる面を並べる。半径は溜まりの広さ。
SEEDS = [
    ("上野公園",         35.71538, 139.77340, 420),
    ("東京国立博物館",   35.71889, 139.77639, 300),
    ("国立西洋美術館",   35.71556, 139.77583, 220),
    ("上野の森美術館",   35.71222, 139.77444, 200),
    ("上野動物園",       35.71694, 139.77111, 340),
    ("不忍池",           35.71222, 139.77028, 300),
    ("上野駅",           35.71380, 139.77720, 320),
    ("アメヤ横丁",       35.70830, 139.77440, 300),
    ("御徒町駅",         35.70750, 139.77470, 240),
    ("上野広小路",       35.70830, 139.77220, 240),
    ("京成上野駅",       35.71130, 139.77380, 200),
]
def hav(a1,o1,a2,o2):
    t=math.pi/180
    return 6371000*math.acos(max(-1,min(1,math.sin(a1*t)*math.sin(a2*t)+
           math.cos(a1*t)*math.cos(a2*t)*math.cos((o1-o2)*t))))

STEP=25.0
LAT0,LAT1=35.7010,35.7250; LON0,LON1=139.7620,139.7860
dlat=STEP/110570.0; dlon=STEP/(111320.0*math.cos(35.713*math.pi/180))
ny=int((LAT1-LAT0)/dlat); nx=int((LON1-LON0)/dlon)
mask=[[False]*nx for _ in range(ny)]
for y in range(ny):
    la=LAT0+y*dlat
    for x in range(nx):
        lo=LON0+x*dlon
        for _,sa,so,r in SEEDS:
            if hav(la,lo,sa,so)<=r: mask[y][x]=True; break
# 穴を埋める（外周から届かないセルはコアの中）
out=[[False]*nx for _ in range(ny)]; st=[]
for x in range(nx):
    for y in (0,ny-1):
        if not mask[y][x]: st.append((y,x))
for y in range(ny):
    for x in (0,nx-1):
        if not mask[y][x]: st.append((y,x))
while st:
    y,x=st.pop()
    if out[y][x] or mask[y][x]: continue
    out[y][x]=True
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        b,a=y+dy,x+dx
        if 0<=b<ny and 0<=a<nx and not out[b][a] and not mask[b][a]: st.append((b,a))
filled=0
for y in range(ny):
    for x in range(nx):
        if not mask[y][x] and not out[y][x]: mask[y][x]=True; filled+=1
cells=sum(r.count(True) for r in mask)
print(f'コア領域 {cells} セル = {cells*STEP*STEP/1e6:.2f} km²（穴埋め {filled} セル）')

# 輪郭を marching squares で取り出す
def inside(y,x): return 0<=y<ny and 0<=x<nx and mask[y][x]
segs=[]
for y in range(-1,ny):
    for x in range(-1,nx):
        a=inside(y,x); b=inside(y,x+1); c=inside(y+1,x+1); d=inside(y+1,x)
        pts={'N':(y+1,x+0.5),'S':(y,x+0.5),'W':(y+0.5,x),'E':(y+0.5,x+1)}
        code=(a<<3)|(b<<2)|(c<<1)|d
        table={1:[('W','N')],2:[('N','E')],3:[('W','E')],4:[('S','E')],5:[('W','N'),('S','E')],
               6:[('N','S')],7:[('W','S')],8:[('W','S')],9:[('N','S')],10:[('W','S'),('N','E')],
               11:[('S','E')],12:[('W','E')],13:[('N','E')],14:[('W','N')]}
        for p,q in table.get(code,[]):
            segs.append((pts[p],pts[q]))
# セグメントを繋いで環に
adj={}
for p,q in segs:
    adj.setdefault(p,[]).append(q); adj.setdefault(q,[]).append(p)
rings=[]; seen=set()
for start in adj:
    if start in seen: continue
    ring=[start]; seen.add(start); cur=start; prev=None
    while True:
        nxt=[v for v in adj[cur] if v!=prev and v not in seen]
        if not nxt: break
        prev, cur = cur, nxt[0]; seen.add(cur); ring.append(cur)
    if len(ring)>=8: rings.append(ring)
rings.sort(key=len, reverse=True)
def togeo(p): return [LAT0+p[0]*dlat, LON0+p[1]*dlon]
poly=[togeo(p) for p in rings[0]]
print(f'輪郭 {len(rings)} 本、最大 {len(poly)} 点')

# 検証：メッシュ値がコアの中と外でどう違うか
def ff(la,lo):
    n=d=0.0
    for m in MESH:
        dd=max(150.0,hav(la,lo,m[0],m[1]))
        if dd>2400: continue
        w=1.0/(dd*dd); n+=w*m[2]; d+=w
    return n/d if d else 0
inv=[ff(LAT0+y*dlat,LON0+x*dlon) for y in range(0,ny,6) for x in range(0,nx,6) if mask[y][x]]
outv=[ff(LAT0+y*dlat,LON0+x*dlon) for y in range(0,ny,6) for x in range(0,nx,6) if not mask[y][x]]
print(f'人流の検証  コア内 中央{sorted(inv)[len(inv)//2]:.0f} / コア外 中央{sorted(outv)[len(outv)//2]:.0f}')

json.dump({'seeds':[{'name':n,'lat':la,'lon':lo,'r':r} for n,la,lo,r in SEEDS],
           'polygon':poly, 'area_km2':round(cells*STEP*STEP/1e6,2),
           'grid':{'lat0':LAT0,'lon0':LON0,'dlat':dlat,'dlon':dlon,'nx':nx,'ny':ny},
           'mask':[''.join('1' if c else '0' for c in r) for r in mask]},
          open(os.path.join(G,'..','data','core.json'),'w'), ensure_ascii=False)
print('→ data/core.json')

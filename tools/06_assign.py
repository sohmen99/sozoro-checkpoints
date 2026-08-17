# -*- coding: utf-8 -*-
"""仮チェックポイントの周辺から実在候補を集め、品質基準で採点して割り当てる。"""
import json, csv, io, math, os, re, glob
from collections import defaultdict
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
RADIUS=380.0            # 仮プロットからの探索半径
def hav(a1,o1,a2,o2):
    t=math.pi/180
    return 6371000*math.acos(max(-1,min(1,math.sin(a1*t)*math.sin(a2*t)+math.cos(a1*t)*math.cos(a2*t)*math.cos((o1-o2)*t))))

# ── 候補を集める ───────────────────────────────────────────────
C=[]
NAMED_CAT={'飲食店営業（そば）':'そば','飲食店営業（一般・ラーメン）':'ラーメン',
 '飲食店営業（すし屋）':'すし','飲食店営業（一般・うなぎ）':'うなぎ',
 '飲食店営業（一般・お好み焼きもんじゃ）':'お好み焼き・もんじゃ','飲食店営業（一般・とんかつ）':'とんかつ'}
pool=list(csv.DictReader(io.StringIO(open(os.path.join(D,'pool5093.csv'),'rb').read().decode('utf-8-sig'))))
for r in pool:
    if r['coord_quality']!='point': continue
    kind = NAMED_CAT.get(r['category'])
    if r['layer']=='食べる' and not kind: continue
    C.append({'name':r['name'].strip(),'lat':float(r['lat']),'lon':float(r['lon']),
              'cat': kind or r['category'], 'group':'食' if kind else '文化財',
              'src':r['source'],'ward':r['ward']})
# OSM
CU={'sushi':'すし','soba':'そば','ramen':'ラーメン','unagi':'うなぎ','okonomiyaki':'お好み焼き・もんじゃ',
    'tonkatsu':'とんかつ','udon':'うどん','tempura':'てんぷら','noodle':'麺'}
for e in json.load(open(os.path.join(D,'osm_candidates.json')))['elements']:
    t=e.get('tags',{}); n=(t.get('name') or '').strip()
    la=e.get('lat') or (e.get('center') or {}).get('lat'); lo=e.get('lon') or (e.get('center') or {}).get('lon')
    if not n or la is None: continue
    if t.get('amenity') in ('restaurant','fast_food'):
        cu=(t.get('cuisine') or '').split(';')[0]
        C.append({'name':n,'lat':la,'lon':lo,'cat':CU.get(cu,cu),'group':'食',
                  'src':'OpenStreetMap','ward':'','brand':bool(t.get('brand') or t.get('brand:wikidata'))})
    elif t.get('amenity')=='place_of_worship':
        C.append({'name':n,'lat':la,'lon':lo,'cat':'寺社','group':'寺社','src':'OpenStreetMap','ward':''})
    elif 'historic' in t:
        C.append({'name':n,'lat':la,'lon':lo,'cat':'史跡・記念物','group':'史跡','src':'OpenStreetMap','ward':''})
    elif t.get('leisure') in ('park','garden'):
        C.append({'name':n,'lat':la,'lon':lo,'cat':'公園' if t['leisure']=='park' else '庭園','group':'みどり','src':'OpenStreetMap','ward':''})
    else:
        C.append({'name':n,'lat':la,'lon':lo,'cat':t.get('tourism',''),'group':'見どころ','src':'OpenStreetMap','ward':''})
# 隣接区の文化財（Q5で「もの」を落とす）
NG_CLS=('美術工芸品','歴史資料','絵画','彫跡','彫刻','書跡','典籍','古文書','無形文化財','工芸技術','民俗文化財')
WN={'131075':'墨田区','131083':'江東区','131016':'千代田区','bunkazai':'中央区'}
for f in glob.glob('/private/tmp/claude-501/-Users-shimizukento/6b1d9408-9044-443c-9b62-198ec41e837e/scratchpad/ext/*.csv'):
    raw=open(f,'rb').read()
    for enc in ('utf-8-sig','cp932','utf-8'):
        try: txt=raw.decode(enc); break
        except Exception: pass
    w=WN[next(k for k in WN if k in f)]
    for r in csv.DictReader(io.StringIO(txt)):
        la=next((k for k in r if '緯度' in k),None); lo=next((k for k in r if '経度' in k),None)
        try: p=(float(r[la]),float(r[lo]))
        except Exception: continue
        cls=(r.get('文化財分類') or r.get('種類') or '')
        if any(x in cls for x in NG_CLS): continue
        C.append({'name':r['名称'].strip(),'lat':p[0],'lon':p[1],'cat':cls or '文化財',
                  'group':'文化財','src':f'{w} 文化財一覧','ward':w})
# 重複を落とす
seen=set(); U=[]
for c in C:
    k=(c['name'], round(c['lat'],4), round(c['lon'],4))
    if k in seen: continue
    seen.add(k); U.append(c)
C=U
print(f'候補プール {len(C):,} 件  ' + str({g:sum(1 for c in C if c['group']==g) for g in {x['group'] for x in C}}))

# ── 品質基準で採点（criteria.json の Q1..Q5）────────────────────
CHAIN=re.compile(
 # 回転寿司・寿司チェーン
 "すしざんまい|くら寿司|スシロー|かっぱ寿司|はま寿司|魚べい|元祖寿司|金太楼|磯丸|三崎港|銚子丸|"
 "まぐろ人|まんてん鮨|魚がし日本一|梅丘寿司|海鮮三崎港|京樽|小僧寿し|築地玉寿司|"
 # ラーメン
 "一風堂|一蘭|天下一品|山岡家|町田商店|田所商店|花月嵐|ラーメン二郎|六厘舎|大勝軒|"
 "日高屋|幸楽苑|らあめん花月|野郎ラーメン|東京豚骨拉麺|ばんから|光麺|渡辺|"
 "卍力|用心棒|盛太郎|づゅる麺|博多風龍|らーめん潤|舎鈴|五ノ神|六厘舎|松富|"
 "つじ田|凪|せたが屋|中本|蒙古タンメン|くるり|一幸舎|ばんから|"
 # フードコート・劇場など、店ではない箱
 "拉麺劇場|ラーメン劇場|横丁|フードコート|フードホール|"
 # そば・うどん
 "富士そば|ゆで太郎|小諸そば|そじ坊|嵯峨谷|田舎そば川一|丸亀製麺|はなまるうどん|杵屋|小松庵|"
 # とんかつ・丼・定食
 "かつや|松のや|松乃家|和幸|新宿さぼてん|さぼてん|とんでん|なか卯|吉野家|すき家|"
 "(?<![一-龥])松屋|やよい軒|大戸屋|てんや|天丼てんや|"
 # その他
 "マクドナルド|モスバーガー|ケンタッキー|サイゼリヤ|ガスト|バーミヤン|ジョナサン|デニーズ|"
 "スターバックス|ドトール|タリーズ|コメダ|プロント|サンマルク|ベローチェ|エクセルシオール",
 re.I)

# 系列か単店か、外からは判断がつかない屋号。落とさずに印だけ付けて人に見せる。
CHECK=re.compile("玉寿司|リトルアジア|けん太|わさび|尾張屋|山田屋|もみじ屋|あさだ|"
 "YUZU|Lab|一番寿司|三喜|千祥|大斗|まる竹|ますや")

# 散歩の行き先として重すぎるもの。慰霊・戦災・解剖・墓誌は外す。
HEAVY=re.compile("慰霊|戦没|戦災|殉職|殉難|解剖|墓誌|供養塔|無縁|火葬|斎場|霊園|納骨|分教会|教会")
NAMED6={'そば','ラーメン','すし','うなぎ','お好み焼き・もんじゃ','とんかつ'}
EXTRA={'うどん','てんぷら','麺'}
PLACE_SUF=('寺','院','神社','稲荷','宮','堂','庵','跡','塚','碑','橋','公園','園','門','社')
THING=re.compile(r'(文書|絵図|絵巻|経|記録|扣|証文|資料|一括|附|図$)')
def score(c):
    q={}
    g=c['group']
    if g=='食':
        q['Q1']=1.0 if c['cat'] in NAMED6 else (0.6 if c['cat'] in EXTRA else 0.15)
    else:
        q['Q1']=0.8 if g in ('寺社','文化財','史跡') else (0.6 if g=='みどり' else 0.5)
    n=c['name']; nn=n.replace('　',' ').strip()
    branch = bool(re.search(r'.{2,}店$', nn)) and '本店' not in nn
    q['Q2']=0.0 if (CHAIN.search(n) or c.get('brand')) else (0.35 if branch else 1.0)
    short=len(nn.replace(' ',''))
    q['Q3']=1.0 if short<=8 or re.search(r'[屋庵軒亭寿庄]$',nn) else (0.7 if short<=12 else 0.4)
    q['Q4']=1.0 if (g in ('寺社','史跡','文化財','みどり') and (nn.endswith(PLACE_SUF) or g in ('寺社','みどり'))) \
            else (0.8 if g!='食' else 1.0)
    q['Q5']=0.0 if (THING.search(nn) or HEAVY.search(nn)) else 1.0
    c['needs_check']= bool(CHECK.search(nn)) and g=='食'
    total=q['Q5']*(0.40*q['Q1']+0.28*q['Q2']+0.14*q['Q3']+0.18*q['Q4'])
    return q, round(total,3)
for c in C: c['q'], c['score'] = score(c)
print(f"品質0.6以上 {sum(1 for c in C if c['score']>=0.6):,} 件 / 0.75以上 {sum(1 for c in C if c['score']>=0.75):,} 件")

# ── 割り当て ───────────────────────────────────────────────────
picks185={r['name'].strip() for r in csv.DictReader(open(os.path.join(D,'picks185.csv'),encoding='utf-8'))}
cps=json.load(open(os.path.join(D,'checkpoints.json'),encoding='utf-8'))
taken=set(); out=[]
for cp in cps['checkpoints']:
    near=[]
    for c in C:
        d=hav(cp['lat'],cp['lon'],c['lat'],c['lon'])
        if d>RADIUS: continue
        key=(c['name'],round(c['lat'],4),round(c['lon'],4))
        if key in taken: continue
        # 近さは効かせるが、品質を覆すほどにはしない。
        # 半径いっぱいの候補は品質で約1.5倍ないと勝てない、という効き方。
        fit=c['score']*(1-0.35*(d/RADIUS)**2)
        near.append((fit,d,c,key))
    near.sort(key=lambda x:-x[0])
    cp['candidates_considered']=len(near)
    if not near:
        cp.update({'spot_name':None,'status':'未割当'}); out.append(cp); continue
    fit,d,c,key=near[0]; taken.add(key)
    cp.update({'spot_name':c['name'],'spot_category':c['cat'],'spot_group':c['group'],
        'spot_lat':round(c['lat'],6),'spot_lon':round(c['lon'],6),
        'offset_m':round(d),'quality':c['score'],'q':c['q'],'fit':round(fit,3),
        'source':c['src'],'reuse_185': c['name'] in picks185,
        'needs_check': bool(c.get('needs_check')),
        'runners_up':[{'name':x[2]['name'],'cat':x[2]['cat'],'offset_m':round(x[1]),
                       'quality':x[2]['score'],'fit':round(x[0],3)} for x in near[1:4]],
        'status':'割当'})
    out.append(cp)
ok=[c for c in out if c.get('spot_name')]
print(f"\n割当 {len(ok)}/{len(out)}  再利用 {sum(1 for c in ok if c['reuse_185'])} / 新規 {sum(1 for c in ok if not c['reuse_185'])}")
print('  平均ズレ %.0fm / 最大 %dm' % (sum(c['offset_m'] for c in ok)/len(ok), max(c['offset_m'] for c in ok)))
print('  平均品質 %.2f' % (sum(c['quality'] for c in ok)/len(ok)))
from collections import Counter
print('  帯別:', dict(Counter(c['band'] for c in ok)))
print('  方位:', dict(Counter(c['sector'] for c in ok)))
print('  種別:', dict(Counter(c['spot_group'] for c in ok)))
json.dump({'radius_m':RADIUS,'checkpoints':out}, open(os.path.join(D,'assigned.json'),'w'), ensure_ascii=False)
print('→ data/assigned.json')

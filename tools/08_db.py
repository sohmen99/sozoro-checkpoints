# -*- coding: utf-8 -*-
"""データベースを書き出す。仮プロット→候補→最終選定が追跡できる形にする。"""
import json, csv, os
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
a=json.load(open(os.path.join(D,'assigned.json'),encoding='utf-8'))
E=json.load(open(os.path.join(D,'edges.json')))
QN={'Q1':'名物の一皿がある業種','Q2':'支店ではない単店の屋号','Q3':'短い和の屋号',
    'Q4':'訪ねられる寺社・史跡そのもの','Q5':'「もの」ではなく「場所」'}
def reason(c):
    q=c['q']; s=[]
    if c['spot_group']=='食':
        s.append('名物の一皿の業種' if q['Q1']>=1.0 else ('近い業種' if q['Q1']>=0.6 else '業種は弱い'))
        s.append('単店の屋号' if q['Q2']>=1.0 else ('支店表記あり' if q['Q2']>0 else 'チェーン'))
    else:
        s.append({'寺社':'訪ねられる寺社','史跡':'史跡・記念物','みどり':'公園・庭園',
                  '文化財':'区登録の文化財','見どころ':'見どころ'}.get(c['spot_group'],c['spot_group']))
    if q['Q3']>=1.0: s.append('短い屋号')
    s.append(f"仮プロットから{c['offset_m']}m")
    if c['runners_up']:
        r=c['runners_up'][0]
        s.append(f"次点は{r['name'][:14]}（{r['offset_m']}m・品質{r['quality']}）で、"
                 + ('品質で上回ったため採用' if c['quality']>r['quality'] else '距離で上回ったため採用'))
    return '。'.join(s)+'。'

COLS=['checkpoint_id','band_min','sector','sector_ja','plot_lat','plot_lon',
      'walk_min_from_core','spot_name','spot_category','spot_group','spot_lat','spot_lon',
      'offset_m','Q1','Q2','Q3','Q4','Q5','quality_total','reason','source','origin',
      'neighbours_15min','candidates_considered','needs_check','runner_up_1','runner_up_2','runner_up_3']
rows=[]
for c in a['checkpoints']:
    if not c.get('spot_name'): continue
    ru=(c['runners_up']+[None,None,None])[:3]
    rows.append({'checkpoint_id':c['checkpoint_id'],'band_min':c['band'],'sector':c['sector'],
      'sector_ja':c['sector_ja'],'plot_lat':c['lat'],'plot_lon':c['lon'],
      'walk_min_from_core':c['walk_min_from_core'],'spot_name':c['spot_name'],
      'spot_category':c['spot_category'],'spot_group':c['spot_group'],
      'spot_lat':c['spot_lat'],'spot_lon':c['spot_lon'],'offset_m':c['offset_m'],
      **{k:c['q'][k] for k in ('Q1','Q2','Q3','Q4','Q5')},
      'quality_total':c['quality'],'reason':reason(c),'source':c['source'],
      'origin':'185件から再利用' if c['reuse_185'] else '新規選定',
      'neighbours_15min':len(E.get(c['checkpoint_id'],[])),
      'candidates_considered':c['candidates_considered'],
      'needs_check':'要確認' if c.get('needs_check') else '',
      **{f'runner_up_{i+1}': (f"{r['name']}／{r['cat']}／{r['offset_m']}m／品質{r['quality']}" if r else '')
         for i,r in enumerate(ru)}})
with open(os.path.join(G,'..','checkpoints.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=COLS); w.writeheader(); w.writerows(rows)
print(f'checkpoints.csv  {len(rows)} 行 / {len(COLS)} 列')
json.dump({'criteria':json.load(open(os.path.join(D,'criteria.json'),encoding='utf-8'))['criteria'],
           'checkpoints':rows,'edges':E},
          open(os.path.join(G,'..','checkpoints.json'),'w'), ensure_ascii=False, indent=1)
print('checkpoints.json')

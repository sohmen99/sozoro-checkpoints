# -*- coding: utf-8 -*-
"""マップを書き出す。仮プロットと最終スポットを同じ checkpoint_id で結んで並べる。"""
import json, os
G=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(G,'..','data')
core=json.load(open(os.path.join(D,'core.json'),encoding='utf-8'))
bands=json.load(open(os.path.join(D,'bands.json')))
db=json.load(open(os.path.join(G,'..','checkpoints.json'),encoding='utf-8'))
payload={'core':{'polygon':core['polygon'],'seeds':core['seeds'],'area':core['area_km2']},
         'bands':bands['rings'],'checkpoints':db['checkpoints'],
         'criteria':db['criteria'],'edges':db['edges']}
open(os.path.join(D,'map_payload.json'),'w').write(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
size=os.path.getsize(os.path.join(D,'map_payload.json'))/1024
print(f'地図データ {size:.0f}KB')

HTML = '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>そぞろ チェックポイント盤</title>
<meta name="description" content="上野の混雑コアから徒歩7分刻みに置いた仮チェックポイント88点と、各点に割り当てた実在スポット。">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><text y=%2226%22 font-size=%2226%22>&#129517;</text></svg>">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--ink:#1A1C20;--mid:#5A6068;--faint:#8C9299;--rule:#E0DCD4;--bg:#F6F4EF;--panel:#FFFDF8;
 --b7:#7A2E2E;--b14:#A8552B;--b21:#8A7420;--b28:#3F6F4F;--b35:#2E4E7A;--plot:#9AA0A8;--core:#B3261E}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font-family:"Hiragino Sans","Yu Gothic","Noto Sans JP",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
#wrap{display:grid;grid-template-columns:376px 1fr;height:100%}
#side{overflow-y:auto;background:var(--panel);border-right:1px solid var(--rule);padding:20px 18px 60px}
#map{height:100%}
h1{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;font-size:23px;margin:0 0 3px;letter-spacing:.05em}
.sub{margin:0 0 16px;font-size:12px;color:var(--mid);line-height:1.7}
.mono{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px}
.stat{background:var(--bg);border:1px solid var(--rule);border-radius:5px;padding:9px 10px}
.stat b{display:block;font-family:ui-monospace,Menlo,monospace;font-size:19px;line-height:1.2}
.stat span{font-size:10px;letter-spacing:.1em;color:var(--faint)}
h2{font-size:11px;letter-spacing:.14em;color:var(--faint);margin:18px 0 8px;font-weight:600;font-family:inherit}
.legend div{display:flex;align-items:center;gap:8px;font-size:12px;padding:3px 0}
.sw{width:22px;height:4px;border-radius:2px;flex:0 0 auto}
.dot{width:11px;height:11px;border-radius:50%;flex:0 0 auto}
.toggles label{display:flex;align-items:center;gap:7px;font-size:12.5px;padding:4px 0;cursor:pointer}
.crit{border:1px solid var(--rule);border-radius:5px;padding:10px 11px;margin-bottom:7px;background:var(--bg)}
.crit b{font-size:12.5px}
.crit p{margin:4px 0 0;font-size:11px;color:var(--mid);line-height:1.65}
.crit code{font-size:10.5px;background:var(--panel);padding:1px 4px;border-radius:3px}
#list{list-style:none;margin:0;padding:0}
#list li{border-bottom:1px solid var(--rule);padding:8px 0;cursor:pointer;display:grid;
 grid-template-columns:auto 1fr auto;gap:8px;align-items:baseline;font-size:12.5px}
#list li:hover{background:var(--bg)}
#list .id{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:var(--faint)}
#list .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#list .bd{font-family:ui-monospace,Menlo,monospace;font-size:10.5px}
.leaflet-popup-content{margin:12px 14px;font-size:12.5px;line-height:1.7;min-width:250px}
.leaflet-popup-content h3{margin:0 0 2px;font-size:15px}
.leaflet-popup-content .k{font-size:10.5px;letter-spacing:.1em;color:#8C9299}
.leaflet-popup-content table{border-collapse:collapse;margin:8px 0;font-size:11.5px;width:100%}
.leaflet-popup-content td{padding:2px 0;vertical-align:top}
.leaflet-popup-content td:first-child{color:#8C9299;padding-right:10px;white-space:nowrap}
.leaflet-popup-content .why{margin:8px 0 0;font-size:11.5px;color:#5A6068;line-height:1.7}
@media(max-width:900px){#wrap{grid-template-columns:1fr;grid-template-rows:auto 62vh}#side{max-height:38vh}}
</style>
</head>
<body>
<div id="wrap">
<div id="side">
  <h1>そぞろ チェックポイント盤</h1>
  <p class="sub">上野の混雑コアを面で囲い、その外周から実際の徒歩ネットワークで7分刻みに線を引き、
  店名を見る前に仮チェックポイントを置いた。そのうえで既存185件から抽出した品質基準で、
  各点の周辺から実在スポットを選んでいる。</p>
  <div class="stats" id="stats"></div>

  <h2>表示</h2>
  <div class="toggles" id="toggles"></div>

  <h2>凡例</h2>
  <div class="legend">
    <div><span class="sw" style="background:var(--core)"></span>混雑コア（1.55km²）</div>
    <div><span class="sw" style="background:var(--b7)"></span>徒歩7分</div>
    <div><span class="sw" style="background:var(--b14)"></span>14分</div>
    <div><span class="sw" style="background:var(--b21)"></span>21分</div>
    <div><span class="sw" style="background:var(--b28)"></span>28分</div>
    <div><span class="sw" style="background:var(--b35)"></span>35分</div>
    <div style="margin-top:6px"><span class="dot" style="background:#fff;border:2px dashed #9AA0A8"></span>仮チェックポイント（店名を見る前に置いた位置）</div>
    <div><span class="dot" style="background:#3F6F4F"></span>最終選定スポット</div>
  </div>

  <h2>185件から抽出した品質基準</h2>
  <div id="crit"></div>

  <h2>チェックポイント一覧</h2>
  <ul id="list"></ul>
</div>
<div id="map"></div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = __PAYLOAD__;
const BC = {7:'#7A2E2E',14:'#A8552B',21:'#8A7420',28:'#3F6F4F',35:'#2E4E7A'};
const map = L.map('map',{zoomControl:true}).setView([35.7195,139.7830],14);
L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
  {attribution:'地理院タイル｜候補: 台東区・荒川区・墨田区・江東区・千代田区・中央区 オープンデータ／OpenStreetMap contributors',maxZoom:18,opacity:.9}).addTo(map);

const L_core=L.layerGroup().addTo(map), L_band=L.layerGroup().addTo(map),
      L_plot=L.layerGroup().addTo(map), L_spot=L.layerGroup().addTo(map),
      L_link=L.layerGroup().addTo(map);

L.polygon(DATA.core.polygon,{color:'#B3261E',weight:2,fillColor:'#B3261E',fillOpacity:.14,
  dashArray:'1'}).bindPopup('<h3>混雑コア</h3><span class="k">'+DATA.core.area+' km²</span>'+
  '<p class="why">'+DATA.core.seeds.map(s=>s.name).join('・')+' を内包する面。'+
  'ここを0分としてすべての徒歩時間を測っている。</p>').addTo(L_core);

[35,28,21,14,7].forEach(b=>{
  (DATA.bands[b]||[]).forEach(ring=>{
    L.polyline(ring.concat([ring[0]]),{color:BC[b],weight:1.9,opacity:.85}).addTo(L_band)
      .bindTooltip('徒歩'+b+'分',{sticky:true});
  });
});

const markers={};
DATA.checkpoints.forEach(c=>{
  L.circleMarker([c.plot_lat,c.plot_lon],{radius:4,color:'#9AA0A8',weight:1.5,
    fillColor:'#fff',fillOpacity:1,dashArray:'2'}).addTo(L_plot)
    .bindTooltip(c.checkpoint_id+' 仮プロット（'+c.band_min+'分・'+c.sector_ja+'）');
  L.polyline([[c.plot_lat,c.plot_lon],[c.spot_lat,c.spot_lon]],
    {color:BC[c.band_min],weight:1.4,opacity:.7,dashArray:'3 3'}).addTo(L_link);
  const q=['Q1','Q2','Q3','Q4','Q5'].map(k=>k+' '+c[k]).join(' ／ ');
  const m=L.circleMarker([c.spot_lat,c.spot_lon],{radius:7,color:'#fff',weight:2,
    fillColor:BC[c.band_min],fillOpacity:.95}).addTo(L_spot).bindPopup(
    '<h3>'+c.spot_name+'</h3>'+
    '<span class="k">'+c.checkpoint_id+' ／ '+c.spot_category+' ／ '+c.spot_group+'</span>'+
    '<table>'+
    '<tr><td>時間帯</td><td>混雑コアから徒歩 '+c.band_min+' 分（実測 '+c.walk_min_from_core+' 分）</td></tr>'+
    '<tr><td>方位</td><td>'+c.sector_ja+'（'+c.sector+'）</td></tr>'+
    '<tr><td>仮プロットからのズレ</td><td>'+c.offset_m+' m</td></tr>'+
    '<tr><td>品質</td><td>'+c.quality_total+' 〔'+q+'〕</td></tr>'+
    '<tr><td>15±7分の隣接</td><td>'+c.neighbours_15min+' 地点</td></tr>'+
    '<tr><td>比較した候補</td><td>'+c.candidates_considered+' 件</td></tr>'+
    '<tr><td>出典</td><td>'+c.source+'</td></tr>'+
    '<tr><td>由来</td><td>'+c.origin+'</td></tr>'+
    '</table><p class="why">'+c.reason+'</p>'+
    (c.runner_up_1?'<p class="why"><b>次点</b><br>'+[c.runner_up_1,c.runner_up_2,c.runner_up_3].filter(Boolean).join('<br>')+'</p>':''));
  markers[c.checkpoint_id]=m;
});

const st=[['88','チェックポイント'],['5','徒歩時間帯'],['8','方位'],
          [Math.round(DATA.checkpoints.reduce((a,c)=>a+c.offset_m,0)/DATA.checkpoints.length)+'m','仮プロットからの平均ズレ'],
          [(DATA.checkpoints.reduce((a,c)=>a+c.quality_total,0)/DATA.checkpoints.length).toFixed(2),'平均品質'],
          [DATA.checkpoints.filter(c=>c.neighbours_15min>=3).length+'/88','15±7分で3つ以上つながる']];
document.getElementById('stats').innerHTML=st.map(([a,b])=>'<div class="stat"><b>'+a+'</b><span>'+b+'</span></div>').join('');
document.getElementById('crit').innerHTML=DATA.criteria.map(c=>
  '<div class="crit"><b>'+c.id+' '+c.name+'</b><p>'+c.why+'</p><p><code>'+c.test+'</code></p></div>').join('');
const layers={'混雑コア':L_core,'徒歩時間帯':L_band,'仮チェックポイント':L_plot,'対応線':L_link,'最終スポット':L_spot};
document.getElementById('toggles').innerHTML=Object.keys(layers).map((k,i)=>
  '<label><input type="checkbox" data-l="'+i+'" checked> '+k+'</label>').join('');
document.querySelectorAll('#toggles input').forEach((el,i)=>el.addEventListener('change',()=>{
  const lg=Object.values(layers)[i]; el.checked?map.addLayer(lg):map.removeLayer(lg);}));
document.getElementById('list').innerHTML=DATA.checkpoints.map(c=>
  '<li data-id="'+c.checkpoint_id+'"><span class="id">'+c.checkpoint_id+'</span>'+
  '<span class="nm">'+c.spot_name+'</span>'+
  '<span class="bd" style="color:'+BC[c.band_min]+'">'+c.band_min+'分 '+c.sector_ja+'</span></li>').join('');
document.querySelectorAll('#list li').forEach(li=>li.addEventListener('click',()=>{
  const m=markers[li.dataset.id]; map.setView(m.getLatLng(),17); m.openPopup();}));
</script>
</body>
</html>
'''
open(os.path.join(G,'..','index.html'),'w',encoding='utf-8').write(
    HTML.replace('__PAYLOAD__', json.dumps(payload, ensure_ascii=False, separators=(',',':'))))
print('→ index.html', round(os.path.getsize(os.path.join(G,'..','index.html'))/1024), 'KB')

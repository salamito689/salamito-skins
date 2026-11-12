"""Render a standalone, responsive, non-transactional Salamito staging catalog."""
import json
from html import escape
from pathlib import Path

SOURCE = Path("uuskins-prices-brl-staging.json")
OUTPUT = Path("uuskins-brl-simulation.html")

def main():
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    if payload.get("simulation_only") is not True or payload.get("currency_verification") != "unverified_assumption_usd":
        raise ValueError("USD simulation flag required")
    if payload.get("production") is not False or payload.get("checkout_enabled") is not False:
        raise ValueError("Production/checkout must be disabled")
    items = payload.get("listings")
    if not isinstance(items, list) or not items:
        raise ValueError("Empty sample")
    quotes = payload["wise_quotes"]
    icon_file = Path("representative-images/manifest.json")
    icons = {}
    if icon_file.is_file():
        icon_manifest = json.loads(icon_file.read_text(encoding="utf-8"))
        if icon_manifest.get("representative_only") is True and icon_manifest.get("schema_version") == 1:
            icons = icon_manifest.get("images", {})
    icon_json = json.dumps(icons, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    # Embedded JSON is escaped for script context. No network, images or checkout.
    embedded = json.dumps(items, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    usd = escape(str(quotes["USD/CNY"]["rate"]))
    cny = escape(str(quotes["CNY/BRL"]["rate"]))
    html = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Salamito Skins | Catálogo de testes</title>
<style>
:root{color-scheme:dark;--bg:#080f1e;--panel:#111c30;--panel2:#17243a;--line:#28374f;--text:#edf5ff;--muted:#9baecb;--blue:#42b5ff;--blue2:#196cfa}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 75% -15%,#193e76 0,transparent 42%),var(--bg);font:14px system-ui,-apple-system,Segoe UI,sans-serif;color:var(--text)}
header{border-bottom:1px solid var(--line);background:#0b1526ee;position:sticky;top:0;z-index:4;backdrop-filter:blur(14px)}.wrap{max-width:1450px;margin:auto;padding:0 26px}.top{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:18px}.logo{font-size:25px;font-weight:850;letter-spacing:-1.1px;color:#fff}.logo span{background:linear-gradient(90deg,#a2e8ff,#42b5ff,#196cfa);background-clip:text;color:transparent}.top small{color:var(--muted)}.warning{background:#30271b;border:1px solid #90612a;color:#ffd79a;border-radius:12px;padding:13px 16px;margin:24px 0 12px;font-weight:650}.hero{padding:18px 0 26px;display:flex;align-items:end;justify-content:space-between;gap:15px;flex-wrap:wrap}h1{font-size:32px;letter-spacing:-1.1px;margin:0 0 9px}p{margin:0;color:var(--muted);line-height:1.6}.count{font-size:13px;color:var(--muted)}.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:22px;padding-bottom:60px}.sidebar,.toolbar{background:#111c30;border:1px solid var(--line);border-radius:15px;padding:19px}.sidebar{align-self:start}.sidebar h2{font-size:15px;margin:0 0 20px}.field{display:block;margin:15px 0 7px;color:#b8c8e0;font-size:12px;font-weight:700}input,select{width:100%;background:#0c1729;color:var(--text);border:1px solid #334661;border-radius:9px;padding:11px;font:inherit;outline:none}input:focus,select:focus{border-color:var(--blue)}.toolbar{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:16px}.toolbar input{max-width:490px}.toolbar select{max-width:220px}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}.card{background:linear-gradient(155deg,#182842,#101b2f);border:1px solid #2a3b56;border-radius:15px;overflow:hidden;min-width:0}.visual{height:150px;display:grid;place-items:center;background:radial-gradient(circle at 50% 55%,#2a4c7a 0,transparent 62%),#101c30;position:relative}.visual .symbol{font-size:53px;opacity:.55;filter:grayscale(1)}.visual img{width:100%;height:100%;object-fit:contain;padding:20px 12px}.inspect{display:block;margin-top:12px;padding:9px 8px;border:1px solid #388cda;border-radius:8px;color:#9edbff;text-align:center;text-decoration:none;font-weight:700}.visual .tag{position:absolute;top:12px;left:12px;font-size:10px;color:#a9c4e8;background:#182d4d;border:1px solid #35547b;padding:6px 8px;border-radius:6px}.body{padding:16px}.name{font-weight:750;line-height:1.4;min-height:42px;font-size:13px}.meta{display:flex;justify-content:space-between;gap:10px;color:#a9bad3;font-size:11px;margin:15px 0}.price{font-size:23px;color:#fff;font-weight:850;letter-spacing:-.5px}.price small{display:block;color:#8da7c9;font-size:10px;font-weight:500;margin-top:5px;letter-spacing:0}.id{font-size:10px;color:#788ea9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:13px}.footer{border-top:1px solid var(--line);margin-top:13px;padding-top:11px;color:#91a9ca;font-size:11px}.empty{grid-column:1/-1;padding:60px 20px;text-align:center;color:var(--muted)}.footnote{margin:18px 0 40px;color:#8196b2;font-size:12px}.rate{font-size:12px;color:#9bb1d0;margin:0 0 20px}
@media(max-width:1200px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:950px){.layout{grid-template-columns:1fr}.sidebar{display:grid;grid-template-columns:repeat(3,1fr);gap:0 14px}.sidebar h2{grid-column:1/-1}.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:650px){.wrap{padding:0 15px}.top{min-height:65px}.top small{display:none}.logo{font-size:21px}.hero h1{font-size:25px}.sidebar{grid-template-columns:1fr 1fr}.toolbar{flex-wrap:wrap}.toolbar input,.toolbar select{max-width:none}.cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.visual{height:120px}.body{padding:11px}.price{font-size:19px}.meta{display:block;line-height:1.9}}@media(max-width:370px){.cards{grid-template-columns:1fr}}
</style></head><body><header><div class="wrap top"><div class="logo">Salamito <span>Skins</span></div><small>Início &nbsp; · &nbsp; Catálogo experimental &nbsp; · &nbsp; Feedbacks</small></div></header>
<main class="wrap"><div class="warning">⚠ SIMULAÇÃO — moeda USD não confirmada. Valores apenas para testes. Não utilizar para vendas. Amostra parcial da UUSKINS; não representa todo o estoque.</div>
<section class="hero"><div><h1>Explore as skins disponíveis</h1><p>Catálogo experimental com anúncios individuais, float e pattern reais da UUSKINS.</p></div><div class="count" id="count"></div></section>
<p class="rate">Wise USD/CNY: __USD__ &nbsp; · &nbsp; Wise CNY/BRL: __CNY__ &nbsp; · &nbsp; Acréscimos: 1% + R$ 0,025/CNY &nbsp; · &nbsp; Cotação histórica, não ao vivo.</p>
<div class="layout"><aside class="sidebar"><h2>Filtros</h2><div><label class="field" for="model">Modelo</label><select id="model"><option value="">Todos os modelos</option></select></div><div><label class="field" for="min">Float mínimo</label><input id="min" type="number" min="0" max="1" step="0.00001" placeholder="0.00000"></div><div><label class="field" for="max">Float máximo</label><input id="max" type="number" min="0" max="1" step="0.00001" placeholder="1.00000"></div><div><label class="field" for="pattern">Pattern</label><input id="pattern" type="number" min="0" step="1" placeholder="Ex.: 714"></div><div><label class="field" for="priceMax">Preço máximo (R$)</label><input id="priceMax" type="number" min="0" step="0.01" placeholder="Sem limite"></div></aside>
<div><div class="toolbar"><input id="search" type="search" placeholder="Buscar skin, float, pattern ou ID..."><select id="sort" aria-label="Ordenar"><option value="price">Menor preço da amostra</option><option value="desc">Maior preço</option><option value="float">Menor float</option><option value="name">Nome A–Z</option></select></div><div class="cards" id="cards"></div><p class="footnote">Imagens ilustrativas do modelo, não do anúncio específico. Adesivos e aparência podem diferir. Não há botão de compra.</p></div></div></main>
<script id="data" type="application/json">__DATA__</script><script id="images" type="application/json">__IMAGES__</script>
<script>
const items=JSON.parse(document.getElementById('data').textContent),images=JSON.parse(document.getElementById('images').textContent),el=id=>document.getElementById(id);
const money=new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
const models=[...new Set(items.map(x=>x.market_hash_name))].sort((a,b)=>a.localeCompare(b));
for(const m of models){const opt=document.createElement('option');opt.value=m;opt.textContent=m;el('model').append(opt)}
function safe(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function visual(x){
 const url=images[x.market_hash_name];
 if(typeof url==='string'&&url.startsWith('https://community.fastly.steamstatic.com/economy/image/')&&/^[a-zA-Z0-9_/-]+$/.test(url.split('/image/')[1]))
   return '<img loading="lazy" alt="Imagem ilustrativa do modelo" src="'+safe(url)+'">';
 return '<span class="symbol" aria-hidden="true">◇</span>';
}
function inspectButton(x){
 const code=x.inspect_embed_code;
 if(typeof code!=='string'||code.length<24||code.length>4096||code.length%2||!/^[a-fA-F0-9]+$/.test(code))return '';
 return '<a class="inspect" href="steam://run/730/en/+csgo_econ_action_preview%20'+code+'">Inspecionar no CS2</a>';
}
function render(){
 const q=el('search').value.trim().toLowerCase(),model=el('model').value,min=el('min').value,max=el('max').value,pattern=el('pattern').value,cap=el('priceMax').value;
 let data=items.filter(x=>(!model||x.market_hash_name===model)&&(!min||Number(x.float)>=Number(min))&&(!max||Number(x.float)<=Number(max))&&(!pattern||String(x.paint_seed)===pattern)&&(!cap||Number(x.price_brl)<=Number(cap))&&(!q||[x.market_hash_name,x.float,x.paint_seed,x.id].some(v=>String(v).toLowerCase().includes(q))));
 const sort=el('sort').value;data.sort((a,b)=>sort==='desc'?Number(b.price_brl)-Number(a.price_brl):sort==='float'?Number(a.float)-Number(b.float):sort==='name'?a.market_hash_name.localeCompare(b.market_hash_name):Number(a.price_brl)-Number(b.price_brl));
 el('count').textContent=data.length+' de '+items.length+' anúncios na amostra';
 el('cards').innerHTML=data.length?data.map(x=>'<article class="card"><div class="visual"><span class="tag">IMAGEM ILUSTRATIVA</span>'+visual(x)+'</div><div class="body"><div class="name">'+safe(x.market_hash_name)+'</div><div class="meta"><span>Float: '+safe(Number(x.float).toFixed(8))+'</span><span>Pattern: '+safe(x.paint_seed)+'</span></div><div class="price">'+money.format(Number(x.price_brl))+'<small>Simulação em reais · não disponível para compra</small></div><div class="id" title="'+safe(x.id)+'">ID: '+safe(x.id)+'</div><div class="footer">UUSKINS · anúncio individual</div>'+inspectButton(x)+'</div></article>').join(''):'<div class="empty">Nenhum anúncio encontrado nesta amostra. Ajuste os filtros.</div>';
}
for(const id of ['search','model','min','max','pattern','priceMax','sort'])el(id).addEventListener('input',render);
render();
</script></body></html>"""
    html = html.replace("__DATA__", embedded).replace("__IMAGES__", icon_json).replace("__USD__", usd).replace("__CNY__", cny)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Generated standalone Salamito card catalog with {len(items)} sampled listings; no production write")

if __name__ == "__main__":
    main()

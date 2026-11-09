#!/usr/bin/env node
// API local de ofertas Salamito. NAO coleta dados da YouPin nem da JA1Skins.
// node scripts/listings-api.cjs [porta] [estado.json] [fx.json]
const http = require('node:http');
const fs = require('node:fs');
const port = Number(process.argv[2] || 8787);
const statePath = process.argv[3] || 'data/youpin-live-state.json';
const fxPath = process.argv[4] || 'fx.json';
const MAX_AGE_MS = 15 * 60 * 1000;
const PRICE_FEE = 1.01, FX_BUFFER = 0.025;
function json(res, code, payload) {
  res.writeHead(code, { 'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','Access-Control-Allow-Origin':'*' });
  res.end(JSON.stringify(payload));
}
function read(path) { return JSON.parse(fs.readFileSync(path, 'utf8')); }
function load() {
  const state = read(statePath), fx = read(fxPath);
  const captured = Date.parse(state.captured_at), fxAt = Date.parse(fx.fetched_at);
  if (state.complete_inventory !== true || !Array.isArray(state.listings) ||
      !Number.isFinite(captured) || captured > Date.now() + 300000 || Date.now()-captured > MAX_AGE_MS)
    throw Error('Inventario ausente, parcial ou desatualizado');
  if (!(Number(fx.rate)>0) || !Number.isFinite(fxAt) || Date.now()-fxAt > 36*3600000 || fxAt>Date.now()+300000)
    throw Error('Cambio indisponivel ou desatualizado');
  return {state,rate:Number(fx.rate)};
}
const server = http.createServer((req,res)=>{
  if (req.method !== 'GET') return json(res,405,{error:'Method not allowed'});
  const u = new URL(req.url,'http://localhost');
  if (u.pathname==='/health') {
    try { const {state}=load();return json(res,200,{status:'ready',captured_at:state.captured_at,count:state.listings.length}); }
    catch(e){return json(res,503,{status:'unavailable',error:e.message});}
  }
  if (u.pathname!=='/api/offers') return json(res,404,{error:'Not found'});
  try {
    const {state,rate}=load();
    const name=u.searchParams.get('market_hash_name');
    if (!name) return json(res,400,{error:'market_hash_name obrigatorio'});
    const page=Number(u.searchParams.get('page')||1), pageSize=Number(u.searchParams.get('pageSize')||20);
    if (!Number.isInteger(page)||page<1||!Number.isInteger(pageSize)||pageSize<1||pageSize>100)
      return json(res,400,{error:'Paginacao invalida'});
    const floatMin=u.searchParams.has('floatMin')?Number(u.searchParams.get('floatMin')):0;
    const floatMax=u.searchParams.has('floatMax')?Number(u.searchParams.get('floatMax')):1;
    const seed=u.searchParams.has('paintSeed')?Number(u.searchParams.get('paintSeed')):null;
    if (!Number.isFinite(floatMin)||!Number.isFinite(floatMax)||floatMin<0||floatMax>1||floatMin>floatMax||
        (seed!==null&&(!Number.isInteger(seed)||seed<0||seed>1000)))
      return json(res,400,{error:'Filtros invalidos'});
    const offers=state.listings.filter(x=>x.market_hash_name===name && x.float>=floatMin && x.float<=floatMax &&
      (seed===null||x.paint_seed===seed)).map(x=>({
        listingId:x.id,priceBrl:Number((x.price_cny*PRICE_FEE*(rate+FX_BUFFER)).toFixed(2)),
        priceCny:x.price_cny,float:String(x.float),paintSeed:x.paint_seed,inspectUrl:x.inspect_link
      })).sort((a,b)=>a.priceBrl-b.priceBrl||a.listingId.localeCompare(b.listingId));
    return json(res,200,{market_hash_name:name,page,pageSize,sourceTotalCount:offers.length,
      captured_at:state.captured_at,offers:offers.slice((page-1)*pageSize,page*pageSize)});
  } catch(e){return json(res,503,{error:'Ofertas indisponiveis',reason:e.message});}
});
if (require.main===module) server.listen(port,()=>console.log('API de testes: http://localhost:'+port));
module.exports={server};

const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process'),net=require('node:net');
const api=path.resolve(__dirname,'listings-api.cjs');
function reservePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.once('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
async function setup(state,fx){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'salamito-api-'));
 const statePath=path.join(dir,'state.json'),fxPath=path.join(dir,'fx.json');
 fs.writeFileSync(statePath,JSON.stringify(state));fs.writeFileSync(fxPath,JSON.stringify(fx));
 const port=await reservePort(),child=cp.spawn(process.execPath,[api,String(port),statePath,fxPath],{stdio:'ignore'});
 for(let i=0;i<100;i++){if(child.exitCode!==null)throw Error('API encerrou');try{await fetch('http://127.0.0.1:'+port+'/health');break;}catch{await new Promise(r=>setTimeout(r,30));}}
 return {base:'http://127.0.0.1:'+port,close(){child.kill();fs.rmSync(dir,{recursive:true,force:true});}};
}
const now=()=>new Date().toISOString();
const item=(id,price,seed,fl)=>({id,market_hash_name:'AK-47 | Test (Field-Tested)',price_cny:price,paint_seed:seed,float:fl,inspect_link:'steam://rungame/730/123/+csgo_econ_action_preview%20S1A2D3'});
test('retorna ofertas reais da entrada, ordenadas, com cambio e filtros',async()=>{
 const s=await setup({complete_inventory:true,captured_at:now(),listings:[item('2',400,50,.4),item('1',300,60,.2)]},{rate:.8,fetched_at:now()});
 try{
  const r=await fetch(s.base+'/api/offers?market_hash_name='+encodeURIComponent('AK-47 | Test (Field-Tested)'));
  assert.equal(r.status,200);const d=await r.json();assert.equal(d.sourceTotalCount,2);
  assert.equal(d.offers[0].listingId,'1');assert.equal(d.offers[0].priceBrl,249.98);
  const f=await fetch(s.base+'/api/offers?market_hash_name='+encodeURIComponent('AK-47 | Test (Field-Tested)')+'&paintSeed=50&floatMin=0.3');
  assert.equal((await f.json()).offers[0].listingId,'2');
 }finally{s.close();}
});
test('recusa inventario antigo e nao expõe ofertas',async()=>{
 const s=await setup({complete_inventory:true,captured_at:'2020-01-01T00:00:00Z',listings:[item('1',300,50,.4)]},{rate:.8,fetched_at:now()});
 try{const r=await fetch(s.base+'/api/offers?market_hash_name=test');assert.equal(r.status,503);assert.equal((await r.json()).error,'Ofertas indisponiveis');}
 finally{s.close();}
});
test('recusa inventario parcial',async()=>{
 const s=await setup({complete_inventory:false,captured_at:now(),listings:[item('1',300,50,.4)]},{rate:.8,fetched_at:now()});
 try{assert.equal((await fetch(s.base+'/health')).status,503);}finally{s.close();}
});

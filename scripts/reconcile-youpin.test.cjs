const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const script=path.resolve(__dirname,'reconcile-youpin.cjs');
const inspect='steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S123A456D789';
function listing(id,price=300){return {id,market_hash_name:'AK-47 | Test (Field-Tested)',price_cny:price,float:0.2,paint_seed:50,inspect_link:inspect};}
function run(feed,prev={listings:[]}) {
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'salamito-'));
 try {
  const i=path.join(dir,'in.json'),p=path.join(dir,'prev.json'),o=path.join(dir,'out.json');
  fs.writeFileSync(i,JSON.stringify(feed));fs.writeFileSync(p,JSON.stringify(prev));
  const result=cp.spawnSync(process.execPath,[script,i,p,o],{encoding:'utf8'});
  return {result,output:fs.existsSync(o)?JSON.parse(fs.readFileSync(o,'utf8')):null};
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
}
const feed=(listings,complete=true)=>({complete_inventory:complete,captured_at:new Date().toISOString(),listings});
test('adiciona anuncios com inventario completo',()=>{
 const r=run(feed([listing('123')]));assert.equal(r.result.status,0);assert.deepEqual(r.output.changes.added,['123']);
});
test('detecta alteracoes e exclusoes por ID',()=>{
 const r=run(feed([listing('123',301)]),{listings:[listing('123',300),listing('456')]});
 assert.equal(r.result.status,0);assert.deepEqual(r.output.changes.updated,['123']);assert.deepEqual(r.output.changes.removed,['456']);
});
test('rejeita inventario parcial',()=>{const r=run(feed([listing('123')],false));assert.notEqual(r.result.status,0);assert.equal(r.output,null);});
test('rejeita captura antiga',()=>{const f=feed([listing('123')]);f.captured_at='2020-01-01T00:00:00Z';assert.notEqual(run(f).result.status,0);});
test('rejeita IDs duplicados',()=>{assert.notEqual(run(feed([listing('123'),listing('123')])).result.status,0);});
test('rejeita inspect ausente',()=>{const x=listing('123');delete x.inspect_link;assert.notEqual(run(feed([x])).result.status,0);});

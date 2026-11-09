const seen=new Map(),status=document.getElementById("status"),save=document.getElementById("save"),fx=document.getElementById("fx"),tabs=document.getElementById("tabs"),cards=document.getElementById("cards"),summary=document.getElementById("summary");
const ranges=[[.15,.18],[.18,.21],[.21,.24],[.24,.27],[.27,.38]];let active=0;
function el(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x;}
function group(d){const f=Number(d.float);if(!Number.isFinite(f)||d.float==null)return -1;return ranges.findIndex(([lo,hi],i)=>f>=lo&&(i===ranges.length-1?f<=hi:f<hi));}
function selected(){return [...seen.values()].filter(d=>d.commodityHashName==="AWP | Printstream (Field-Tested)");}
function refresh(){
 status.textContent=seen.size+" anúncio(s) capturado(s) nesta sessão.";save.disabled=!seen.size;
 const all=selected();tabs.replaceChildren();ranges.forEach(([lo,hi],i)=>{const n=all.filter(d=>group(d)===i).length,b=el("button",i===active?"active":"",lo.toFixed(2)+"–"+hi.toFixed(2)+" ("+n+")");b.addEventListener("click",()=>{active=i;refresh()});tabs.append(b)});
 const rows=all.filter(d=>group(d)===active).sort((a,b)=>Number(a.priceCNY)-Number(b.priceCNY)).slice(0,10);
 summary.textContent="Mostrando "+rows.length+" de "+all.filter(d=>group(d)===active).length+" registros capturados nesta faixa (até 10, menor preço primeiro).";
 cards.replaceChildren();if(!rows.length){cards.append(el("p","empty","Nenhum anúncio desta faixa foi capturado ainda."));return;}
 for(const d of rows){
 const c=el("div","card"),pic=el("div"),info=el("div"),price=el("div","price");
 if(d.image&&/^https:\/\//.test(d.image)){const img=el("img");img.src=d.image;img.alt="Imagem informada pela YouPin";img.referrerPolicy="no-referrer";pic.append(img)}else pic.append(el("span","small","Sem imagem individual"));
 const rate=Number(fx.value),cny=Number(d.priceCNY);
 price.textContent=fx.value&&rate>0&&Number.isFinite(cny)?"R$ "+((cny*1.01)*(rate+.025)).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2}):"Preço em R$ indisponível";
 info.append(price,el("div","small","Float: "+(d.float??"—")),el("div","small","Pattern: "+(d.paintSeed??"—")));
 if(typeof d.inspect==="string"&&d.inspect.startsWith("steam://")){const a=el("a","small","Inspecionar no CS2");a.href=d.inspect;info.append(a)}
 c.append(pic,info);cards.append(c);
 }
}
chrome.devtools.network.onRequestFinished.addListener(req=>{try{
 const u=new URL(req.request.url);if(u.hostname!=="pc-api.youpin898.com"||!u.pathname.endsWith("/queryOnSaleCommodityList")||req.response.status!==200)return;
 req.getContent((content,encoding)=>{try{
 if(encoding==="base64")content=atob(content);const j=JSON.parse(content);if(j.Code!==0||!Array.isArray(j.Data))return;
 for(const d of j.Data){if(d.id==null||!d.commodityHashName)continue;seen.set(String(d.id),{id:String(d.id),commodityHashName:d.commodityHashName,priceCNY:d.price??null,float:d.abrade??null,paintSeed:d.paintSeed??null,image:d.iconUrlLarge||d.iconUrl||null,inspect:d.actions||null,capturedAt:new Date().toISOString()})}refresh();
 }catch(e){status.textContent="Resposta recebida, mas não foi possível interpretá-la."}})}catch(e){}});
fx.addEventListener("input",refresh);
save.addEventListener("click",()=>{const payload={source:"YouPin browser observation",availabilityConfirmed:false,createdAt:new Date().toISOString(),count:seen.size,listings:[...seen.values()]};const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="salamito-youpin-captura.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)});
document.getElementById("clear").addEventListener("click",()=>{seen.clear();refresh()});refresh();
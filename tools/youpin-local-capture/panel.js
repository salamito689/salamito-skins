const seen=new Map();const status=document.getElementById("status"),save=document.getElementById("save");
function refresh(){status.textContent=seen.size+" anúncio(s) capturado(s) nesta sessão.";save.disabled=!seen.size;}
chrome.devtools.network.onRequestFinished.addListener(req=>{
 try{
  const u=new URL(req.request.url);
  if(u.hostname!=="pc-api.youpin898.com"||!u.pathname.endsWith("/queryOnSaleCommodityList")||req.response.status!==200)return;
  req.getContent((content,encoding)=>{
   try{
    if(encoding==="base64")content=atob(content);
    const j=JSON.parse(content);
    if(j.Code!==0||!Array.isArray(j.Data))return;
    for(const d of j.Data){if(d.id==null||!d.commodityHashName)continue;
     seen.set(String(d.id),{id:String(d.id),commodityHashName:d.commodityHashName,priceCNY:d.price??null,float:d.abrade??null,paintSeed:d.paintSeed??null,image:d.iconUrlLarge||d.iconUrl||null,inspect:d.actions||null,capturedAt:new Date().toISOString()});}
    refresh();
   }catch(e){status.textContent="Resposta recebida, mas não foi possível interpretá-la.";}
  });
 }catch(e){}
});
save.addEventListener("click",()=>{
 const payload={source:"YouPin browser observation",availabilityConfirmed:false,createdAt:new Date().toISOString(),count:seen.size,listings:[...seen.values()]};
 const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="salamito-youpin-captura.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
});
document.getElementById("clear").addEventListener("click",()=>{seen.clear();refresh();});
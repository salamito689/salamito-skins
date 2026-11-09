// Diagnóstico único e sem autenticação. NÃO sincroniza anúncios e NÃO tenta contornar bloqueios.
const TARGET="https://pc-api.youpin898.com/api/homepage/pc/goods/market/queryOnSaleCommodityList";
export default {
 async fetch(request) {
  const url=new URL(request.url);
  if(url.pathname!=="/diagnostico")return Response.json({service:"Salamito YouPin diagnostic",instructions:"GET /diagnostico para executar um teste único; nenhum dado é publicado."});
  if(request.method!=="GET")return new Response("Method not allowed",{status:405});
  const body={gameId:"730",listType:"10",templateId:"110925",listSortType:1,pageIndex:1,pageSize:10,sortType:0};
  try{
   const response=await fetch(TARGET,{method:"POST",headers:{"content-type":"application/json","accept":"application/json"},body:JSON.stringify(body),redirect:"manual",signal:AbortSignal.timeout(12000)});
   const type=response.headers.get("content-type")||"";
   if(!response.ok)return Response.json({reachable:true,http_status:response.status,content_type:type,authorized_data_access:false,note:"Sem tentativas adicionais ou alteração de cabeçalhos."});
   if(!type.includes("json"))return Response.json({reachable:true,http_status:response.status,content_type:type,valid_listings:false});
   const data=await response.json();
   const first=Array.isArray(data.Data)?data.Data[0]:null;
   return Response.json({reachable:true,http_status:response.status,api_code:data.Code??null,valid_listings:data.Code===0&&Array.isArray(data.Data),returned_count:Array.isArray(data.Data)?data.Data.length:0,has_next:data.HasNext??null,available_fields:first?["id","commodityHashName","price","abrade","paintSeed","actions","iconUrlLarge"].filter(k=>first[k]!=null):[],note:"Resultado técnico. Não comprova permissão para uso comercial nem atualização contínua."});
  }catch(error){return Response.json({reachable:false,error_type:error.name==="TimeoutError"?"timeout":"network_error",valid_listings:false},{status:502})}
 }
};
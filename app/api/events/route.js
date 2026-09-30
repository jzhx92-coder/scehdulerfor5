import {NextResponse} from "next/server";
import {unstable_cache,revalidateTag} from "next/cache";
export const dynamic="force-dynamic";

function plain(prop){
 if(!prop)return "";
 const type=prop.type;
 if(type==="date")return prop.date?.start||"";
 const v=prop[type];
 if(Array.isArray(v))return v.map(x=>x.plain_text||x.name||"").join("");
 if(type==="select")return v?.name||"";
 return typeof v==="string"?v:"";
}

async function queryEvents(id){
 const token=process.env.NOTION_TOKEN;
 const results=[];
  let cursor;
  do{
   const body={page_size:100};
   if(cursor)body.start_cursor=cursor;
   const r=await fetch(`https://api.notion.com/v1/data_sources/${id}/query`,{
    method:"POST",
    headers:{Authorization:`Bearer ${token}`,"Notion-Version":"2025-09-03","Content-Type":"application/json"},
    body:JSON.stringify(body),
    cache:"no-store",
    signal:AbortSignal.timeout(15000)
   });
   if(!r.ok)throw new Error(await r.text());
   const j=await r.json();
   results.push(...j.results);
   cursor=j.has_more?j.next_cursor:null;
  }while(cursor);

  const events=results.map(row=>{
   const p=row.properties||{};
   const auditor=plain(p["도감사관"]);
   return {
    date:plain(p["3차점검일"]),
    school:plain(p["학교명"]),
    people:auditor.split(/[,/]/).map(x=>x.trim()).filter(Boolean)
   };
  }).filter(x=>x.date&&x.school);

  return events.sort((a,b)=>a.date.localeCompare(b.date)||a.school.localeCompare(b.school,"ko"));
}
const cachedEvents=unstable_cache(queryEvents,["audit-events-v1"],{revalidate:60,tags:["audit-events"]});

export async function GET(request){
 const token=process.env.NOTION_TOKEN, id=process.env.NOTION_DATA_SOURCE_ID;
 if(!token||!id)return NextResponse.json({error:"Notion 환경변수가 필요합니다."},{status:500});
 try{
  if(new URL(request.url).searchParams.get("refresh")==="1")revalidateTag("audit-events");
  const events=await cachedEvents(id);
  return NextResponse.json({events},{headers:{"Cache-Control":"no-store"}});
 }catch(e){
  return NextResponse.json({error:"일정을 불러오지 못했습니다.",detail:String(e)},{status:500});
 }
}

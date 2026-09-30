"use client";
import {useEffect,useRef,useState} from "react";
const COLORS=["#7fa7d8","#87b49b","#a996c8","#d1a477","#78aeb0","#c58f9c","#9ead7b","#9a9fc5"];
const key=d=>{const x=new Date(d);return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,"0")}-${String(x.getDate()).padStart(2,"0")}`};
const add=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x};
const color=n=>COLORS[[...(n||"미지정")].reduce((a,ch,i)=>a+ch.charCodeAt(0)*(i+1),0)%COLORS.length];
const short=s=>s.replace(/여자고등학교$/,"고").replace(/여자중학교$/,"여중").replace(/초등학교$/,"초").replace(/중학교$/,"중").replace(/고등학교$/,"고").replace(/유치원$/,"유");
const fmt=d=>`${d.getMonth()+1}월 ${d.getDate()}일`;
const HOLIDAYS_2026=new Set(["2026-01-01","2026-02-16","2026-02-17","2026-02-18","2026-03-01","2026-03-02","2026-05-05","2026-05-24","2026-05-25","2026-06-03","2026-06-06","2026-08-15","2026-08-17","2026-09-24","2026-09-25","2026-09-26","2026-10-03","2026-10-05","2026-10-09","2026-12-25"]);
const isRedDay=d=>d.getDay()===0||d.getDay()===6||HOLIDAYS_2026.has(key(d));
export default function Home(){
 const [events,setEvents]=useState([]),[day,setDay]=useState(new Date()),[week,setWeek]=useState(new Date()),[month,setMonth]=useState(new Date()),[view,setView]=useState("month"),[who,setWho]=useState("전체 일정"),[mine,setMine]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState(""),[hasData,setHasData]=useState(false),[selectedDate,setSelectedDate]=useState(null);
 const pending=useRef(false);
 const load=async(fresh=false)=>{
  if(pending.current)return;
  pending.current=true;setLoading(true);setError("");
  try{
   const r=await fetch(fresh?"/api/events?refresh=1":"/api/events",{cache:"no-store"});
   const j=await r.json();
   if(!r.ok||!Array.isArray(j.events))throw new Error(j.error||"일정을 불러오지 못했습니다.");
   setEvents(j.events);setHasData(true);
   try{sessionStorage.setItem("audit-events-v1",JSON.stringify({events:j.events,savedAt:Date.now()}))}catch{}
  }catch(e){setError(e.message||"일정을 불러오지 못했습니다. 다시 시도해 주세요.")}
  finally{pending.current=false;setLoading(false)}
 };
 useEffect(()=>{
  try{
   const saved=JSON.parse(sessionStorage.getItem("audit-events-v1")||"null");
   if(saved&&Array.isArray(saved.events)&&Date.now()-saved.savedAt<30*60*1000){setEvents(saved.events);setHasData(true)}
  }catch{}
  load();
 },[]);
 const names=[...new Set(events.flatMap(e=>e.people))].sort();
 const filtered=mine&&who!=="전체 일정"?events.filter(e=>e.people.includes(who)):events;
 const todayEvents=events.filter(e=>e.date===key(day));
 const monday=add(week,-((week.getDay()+6)%7)), sunday=add(monday,6);
 const weekEvents=filtered.filter(e=>e.date>=key(monday)&&e.date<=key(sunday)).sort((a,b)=>a.date.localeCompare(b.date)||a.school.localeCompare(b.school,"ko"));
 const y=month.getFullYear(),m=month.getMonth(), first=new Date(y,m,1), blanks=first.getDay(),days=new Date(y,m+1,0).getDate();
 return <main>
  <div className="brand"><i/>자율형종합감사 일정</div>
  <h1>{fmt(new Date())}</h1><div className="sub">오늘</div>
  <Nav title={key(day)===key(new Date())?"오늘의 일정":fmt(day)+" 일정"} prev={()=>setDay(add(day,-1))} next={()=>setDay(add(day,1))}/>
  <section className={"today "+(!todayEvents.length?"empty":"")}>
   <small>{day.getFullYear()}. {day.getMonth()+1}. {day.getDate()}.</small>
   {loading&&!hasData?<b>일정을 불러오는 중입니다…</b>:todayEvents.length?todayEvents.map((e,i)=><div className="todayline" key={i}>{e.school} <span>({e.people.join(" · ")||"미지정"})</span></div>):<><b>예정된 3차 점검이 없습니다</b><p>좌우 화살표로 날짜를 이동하세요.</p></>}
  </section>
  <label>내 이름</label><select value={who} onChange={e=>setWho(e.target.value)}><option>전체 일정</option>{names.map(n=><option key={n}>{n}</option>)}</select>
  <label className="toggle"><input type="checkbox" checked={mine} disabled={who==="전체 일정"} onChange={e=>setMine(e.target.checked)}/> 내 일정만 보기</label>
  <div className="tabs"><button className={view==="week"?"on":""} onClick={()=>setView("week")}>주간</button><button className={view==="month"?"on":""} onClick={()=>setView("month")}>월간</button></div>
  {view==="week"?<><Nav title={`${fmt(monday)} – ${fmt(sunday)}`} prev={()=>setWeek(add(week,-7))} next={()=>setWeek(add(week,7))}/>{loading&&!hasData?<div className="none" role="status">일정을 불러오는 중입니다…</div>:<Cards items={weekEvents}/>}</>:<>
   <Nav title={`${y}년 ${m+1}월`} prev={()=>setMonth(new Date(y,m-1,1))} next={()=>setMonth(new Date(y,m+1,1))}/>
   <div className="calendar"><div className="dows">{["일","월","화","수","목","금","토"].map(x=><b className={x==="토"||x==="일"?"red":""} key={x}>{x}</b>)}</div><div className="grid">{Array.from({length:blanks}).map((_,i)=><div key={"b"+i}/>) }{Array.from({length:days},(_,i)=>i+1).map(d=>{const date=new Date(y,m,d);const es=filtered.filter(e=>e.date===key(date));return <button type="button" className="cell" key={d} aria-label={`${y}년 ${m+1}월 ${d}일 일정 ${es.length}건 보기`} onClick={()=>setSelectedDate(date)}><strong className={isRedDay(date)?"red":""}>{d}</strong>{es.map((e,i)=><span key={i} style={{color:color(e.people[0]),background:color(e.people[0])+"20"}}>{short(e.school)}({e.people.map(p=>p[0]).join("·")})</span>)}</button>})}</div></div>
  </>}
  <p className="calendarhint">월간 달력의 날짜를 누르면 일정을 크게 볼 수 있습니다.</p>
  {selectedDate&&<DayDialog date={selectedDate} items={events.filter(e=>e.date===key(selectedDate))} loading={loading&&!hasData} onClose={()=>setSelectedDate(null)}/>}
  {error&&<p className="error" role="alert">{error}{hasData?" 이전에 불러온 일정을 표시하고 있습니다.":""}</p>}
  <button className="reload" disabled={loading} onClick={()=>load(true)}>{loading?(hasData?"최신 일정 확인 중…":"불러오는 중…"):"↻ 최신 일정 불러오기"}</button>
 </main>
}
function Nav({title,prev,next}){return <div className="nav"><button onClick={prev}>‹</button><b>{title}</b><button onClick={next}>›</button></div>}
function Cards({items}){return <div className="panel">{items.length?items.map((e,i)=><article key={i} style={{borderLeftColor:color(e.people[0])}}><small>{e.date.replaceAll("-",". ")}.</small><b>{e.school}</b><span style={{color:color(e.people[0])}}>{e.people.join(" · ")}</span></article>):<div className="none">예정된 3차 점검이 없습니다.</div>}</div>}

function DayDialog({date,items,loading,onClose}){
 const ref=useRef(null);
 useEffect(()=>{
  const dialog=ref.current;
  dialog.showModal();
  const overflow=document.body.style.overflow;
  document.body.style.overflow="hidden";
  return ()=>{document.body.style.overflow=overflow;dialog.close()};
 },[]);
 return <dialog ref={ref} className="daydialog" aria-labelledby="day-title" onCancel={onClose} onClick={e=>{if(e.target===e.currentTarget)onClose()}}>
  <div className="dialoghead"><h2 id="day-title">{date.getFullYear()}년 {fmt(date)} ({["일","월","화","수","목","금","토"][date.getDay()]})</h2><button type="button" autoFocus aria-label="일정 상세 닫기" onClick={onClose}>×</button></div>
  <p className="dialogcount">{items.length}건의 일정</p>
  {loading?<div className="none">일정을 불러오는 중입니다…</div>:items.length?<ul className="daylist">{items.map((e,i)=><li key={i} style={{color:color(e.people[0])}}>{short(e.school)}({e.people.join(" · ")||"미지정"})</li>)}</ul>:<div className="none">예정된 3차 점검이 없습니다.</div>}
 </dialog>
}

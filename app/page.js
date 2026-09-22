"use client";
import {useEffect,useMemo,useState} from "react";
const COLORS=["#7fa7d8","#87b49b","#a996c8","#d1a477","#78aeb0","#c58f9c","#9ead7b","#9a9fc5"];
const key=d=>{const x=new Date(d);return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,"0")}-${String(x.getDate()).padStart(2,"0")}`};
const add=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x};
const color=n=>COLORS[[...(n||"미지정")].reduce((a,ch,i)=>a+ch.charCodeAt(0)*(i+1),0)%COLORS.length];
const short=s=>s.replace(/여자고등학교$/,"고").replace(/여자중학교$/,"여중").replace(/초등학교$/,"초").replace(/중학교$/,"중").replace(/고등학교$/,"고").replace(/유치원$/,"유");
const fmt=d=>`${d.getMonth()+1}월 ${d.getDate()}일`;
const HOLIDAYS_2026=new Set(["2026-01-01","2026-02-16","2026-02-17","2026-02-18","2026-03-01","2026-03-02","2026-05-05","2026-05-24","2026-05-25","2026-06-03","2026-06-06","2026-08-15","2026-08-17","2026-09-24","2026-09-25","2026-09-26","2026-10-03","2026-10-05","2026-10-09","2026-12-25"]);
const isRedDay=d=>d.getDay()===0||d.getDay()===6||HOLIDAYS_2026.has(key(d));
export default function Home(){
 const [events,setEvents]=useState([]),[day,setDay]=useState(new Date()),[week,setWeek]=useState(new Date()),[month,setMonth]=useState(new Date()),[view,setView]=useState("month"),[who,setWho]=useState("전체 일정"),[mine,setMine]=useState(false),[loading,setLoading]=useState(true);
 const load=()=>{setLoading(true);fetch("/api/events").then(r=>r.json()).then(j=>setEvents(j.events||[])).finally(()=>setLoading(false))};
 useEffect(load,[]);
 const names=[...new Set(events.flatMap(e=>e.people))].sort();
 const filtered=mine&&who!=="전체 일정"?events.filter(e=>e.people.includes(who)):events;
 const todayEvents=events.filter(e=>e.date===key(day));
 const monday=add(week,-((week.getDay()+6)%7)), sunday=add(monday,6);
 const weekEvents=filtered.filter(e=>e.date>=key(monday)&&e.date<=key(sunday));
 const y=month.getFullYear(),m=month.getMonth(), first=new Date(y,m,1), blanks=first.getDay(),days=new Date(y,m+1,0).getDate();
 return <main>
  <div className="brand"><i/>자율형종합감사 일정</div>
  <h1>{fmt(new Date())}</h1><div className="sub">오늘</div>
  <Nav title={key(day)===key(new Date())?"오늘의 일정":fmt(day)+" 일정"} prev={()=>setDay(add(day,-1))} next={()=>setDay(add(day,1))}/>
  <section className={"today "+(!todayEvents.length?"empty":"")}>
   <small>{day.getFullYear()}. {day.getMonth()+1}. {day.getDate()}.</small>
   {todayEvents.length?todayEvents.map((e,i)=><div className="todayline" key={i}>{e.school} <span>({e.people.join(" · ")||"미지정"})</span></div>):<><b>예정된 3차 점검이 없습니다</b><p>좌우 화살표로 날짜를 이동하세요.</p></>}
  </section>
  <label>내 이름</label><select value={who} onChange={e=>setWho(e.target.value)}><option>전체 일정</option>{names.map(n=><option key={n}>{n}</option>)}</select>
  <label className="toggle"><input type="checkbox" checked={mine} disabled={who==="전체 일정"} onChange={e=>setMine(e.target.checked)}/> 내 일정만 보기</label>
  <div className="tabs"><button className={view==="week"?"on":""} onClick={()=>setView("week")}>주간</button><button className={view==="month"?"on":""} onClick={()=>setView("month")}>월간</button></div>
  {view==="week"?<><Nav title={`${fmt(monday)} – ${fmt(sunday)}`} prev={()=>setWeek(add(week,-7))} next={()=>setWeek(add(week,7))}/><Cards items={weekEvents}/></>:<>
   <Nav title={`${y}년 ${m+1}월`} prev={()=>setMonth(new Date(y,m-1,1))} next={()=>setMonth(new Date(y,m+1,1))}/>
   <div className="calendar"><div className="dows">{["일","월","화","수","목","금","토"].map(x=><b className={x==="토"||x==="일"?"red":""} key={x}>{x}</b>)}</div><div className="grid">{Array.from({length:blanks}).map((_,i)=><div key={"b"+i}/>) }{Array.from({length:days},(_,i)=>i+1).map(d=>{const date=new Date(y,m,d);const es=filtered.filter(e=>e.date===key(date));return <div className="cell" key={d}><strong className={isRedDay(date)?"red":""}>{d}</strong>{es.map((e,i)=><span key={i} style={{color:color(e.people[0]),background:color(e.people[0])+"20"}}>{short(e.school)}({e.people.map(p=>p[0]).join("·")})</span>)}</div>})}</div></div>
  </>}
  <button className="reload" onClick={load}>{loading?"불러오는 중…":"↻ 최신 일정 불러오기"}</button>
 </main>
}
function Nav({title,prev,next}){return <div className="nav"><button onClick={prev}>‹</button><b>{title}</b><button onClick={next}>›</button></div>}
function Cards({items}){return <div className="panel">{items.length?items.map((e,i)=><article key={i} style={{borderLeftColor:color(e.people[0])}}><small>{e.date.replaceAll("-",". ")}.</small><b>{e.school}</b><span style={{color:color(e.people[0])}}>{e.people.join(" · ")}</span></article>):<div className="none">예정된 3차 점검이 없습니다.</div>}</div>}

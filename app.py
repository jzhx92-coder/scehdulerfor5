import calendar
from datetime import date, datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="자율형종합감사 일정", page_icon="📅", layout="centered")

NOTION_TOKEN = st.secrets.get("NOTION_TOKEN", "")
DATA_SOURCE_ID = st.secrets.get("NOTION_DATA_SOURCE_ID", "")

def clean_date(value):
    if not value: return None
    if isinstance(value, dict): value = value.get("start")
    value = str(value).strip().replace(". ", "-").replace(".", "-").strip("-")
    try: return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError: return None

def text_value(prop):
    if not isinstance(prop, dict): return str(prop or "")
    kind = prop.get("type")
    parts = prop.get(kind, []) if kind else []
    if kind == "date": return prop.get("date", {})
    if isinstance(parts, list): return "".join(x.get("plain_text", "") for x in parts)
    return str(parts or "")

@st.cache_data(ttl=60, show_spinner=False)
def load_events(token, source_id):
    if not token or not source_id: return []
    headers={"Authorization":f"Bearer {token}","Notion-Version":"2025-09-03","Content-Type":"application/json"}
    response=requests.post(f"https://api.notion.com/v1/data_sources/{source_id}/query",headers=headers,json={"page_size":100},timeout=20)
    response.raise_for_status()
    events=[]
    for row in response.json().get("results",[]):
        props=row.get("properties",{})
        event_date=clean_date(text_value(props.get("3차점검일",{})))
        school=text_value(props.get("학교명",{})).strip()
        people=[x.strip() for x in text_value(props.get("도감사관",{})).replace("/",",").split(",") if x.strip()]
        if event_date and school: events.append({"date":event_date,"school":school,"people":people})
    return sorted(events,key=lambda x:(x["date"],x["school"]))

def fmt_day(d): return f"{d.year}. {d.month}. {d.day}."
def person_text(people): return " · ".join(people) if people else "미지정"

def short_school(name):
    # 긴 명칭부터 처리해야 여자중/여자고가 일반 중/고 규칙에 먹히지 않음
    replacements=[
        ("여자고등학교","고"),
        ("여자중학교","여중"),
        ("초등학교","초"),
        ("중학교","중"),
        ("고등학교","고"),
    ]
    for old,new in replacements:
        if name.endswith(old):
            return name[:-len(old)] + new
    return name

def month_label(event):
    school=short_school(event["school"])
    surnames="·".join(p[0] for p in event["people"] if p)
    return f"{school}({surnames})" if surnames else school

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 50% -10%,#eaf3ff 0,#f5f7fb 38%);color:#182230}
.block-container{max-width:540px;padding:1.35rem 1rem 5rem}
header[data-testid="stHeader"]{background:transparent}
h1{font-size:2.35rem!important;letter-spacing:-.09rem!important;margin:.2rem 0 0!important}
.sub{color:#768196;font-size:1rem;margin:.2rem 0 1.2rem}
.brand{color:#607087;font-size:.82rem;font-weight:750;display:flex;align-items:center;gap:.45rem}
.brand:before{content:"";width:.48rem;height:.48rem;border-radius:50%;background:#30c778;box-shadow:0 0 0 4px #30c77818}
.today{position:relative;overflow:hidden;background:linear-gradient(145deg,#2688ff,#075fd8);color:white;border-radius:1.75rem;padding:1.4rem;box-shadow:0 18px 42px #006be32b;margin:.9rem 0 1rem}
.today.empty{background:linear-gradient(145deg,#fff,#fbfcff);color:#182230;border:1px solid white;box-shadow:0 12px 34px #263e6610}
.kicker{font-size:.88rem;font-weight:750;opacity:.8;margin-bottom:.65rem}.school{font-size:1.4rem;font-weight:850;letter-spacing:-.03rem}.people{font-size:.93rem;opacity:.88;margin-top:.35rem}
div[data-baseweb="select"]>div{border:0!important;border-radius:1rem!important;background:#ffffffdd!important;box-shadow:0 7px 22px #30486f0d!important}
.panel{background:#ffffffea;border:1px solid white;border-radius:1.65rem;padding:1.15rem;box-shadow:0 14px 42px #2038560d;margin-top:.7rem}
.event{position:relative;background:#f3f6fa;border:1px solid #edf0f5;border-radius:1.1rem;padding:.85rem 1rem .85rem 1.15rem;margin:.5rem 0}.event-date{font-size:.78rem;color:#7f8a9a;font-weight:650}.event-school{font-size:1.03rem;font-weight:820;margin-top:.18rem}.event-person{font-size:.87rem;color:#657084;margin-top:.2rem}.none{text-align:center;color:#8a95a6;padding:2rem .5rem}
.stButton button{border-radius:1rem;border:0;font-weight:750}
.navtitle{text-align:center;font-weight:850;font-size:1.05rem}
.cal{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:4px}
.dow{text-align:center;color:#8b96a8;font-size:.72rem;font-weight:750;padding:.2rem 0 .35rem}
.cell{min-height:64px;border-radius:.7rem;padding:.3rem;background:#f6f8fb;border:1px solid #edf0f5;min-width:0;overflow:hidden}
.cell.blank{background:transparent;border-color:transparent}.num{font-size:.76rem;font-weight:750}.dot{width:5px;height:5px;border-radius:50%;background:#1677ff;margin-top:4px}
.cal-school{font-size:.56rem;line-height:1.2;margin-top:3px;font-weight:750;white-space:nowrap;letter-spacing:-.03em;overflow:hidden;text-overflow:clip;border-radius:.32rem;padding:2px 3px}
@media (prefers-color-scheme:dark){
 .stApp{background:radial-gradient(circle at 50% -10%,#101827 0,#0e1117 38%);color:#e5e9f2}
 .today.empty,.panel{background:#15181e;color:#e5e9f2;border-color:#30343b;box-shadow:none}
 .event,.cell{background:#171a20;border-color:#353941}.event-person,.event-date,.sub{color:#8e98aa}
 div[data-baseweb="select"]>div{background:#15181e!important}
}
</style>
""",unsafe_allow_html=True)

today=date.today()
if "today_cursor" not in st.session_state: st.session_state.today_cursor=today
if "month_cursor" not in st.session_state: st.session_state.month_cursor=today

st.markdown('<div class="brand">자율형종합감사 일정</div>',unsafe_allow_html=True)
st.title(f"{today.month}월 {today.day}일")
st.markdown(f'<div class="sub">{today.strftime("%A")} · 오늘</div>',unsafe_allow_html=True)

try:
    all_events=load_events(NOTION_TOKEN,DATA_SOURCE_ID); error=None
except Exception as exc:
    all_events=[]; error=str(exc)

# 오늘의 일정 카드 자체가 일간 탐색기 역할을 함
shown_day=st.session_state.today_cursor
left,center,right=st.columns([1,8,1],vertical_alignment="center")
with left:
    if st.button("‹",key="today_prev",use_container_width=True):
        st.session_state.today_cursor-=timedelta(days=1); st.rerun()
with center:
    label="오늘의 일정" if shown_day==today else f"{shown_day.month}월 {shown_day.day}일 일정"
    st.markdown(f'<div style="text-align:center;font-weight:800;color:#768196">{label}</div>',unsafe_allow_html=True)
with right:
    if st.button("›",key="today_next",use_container_width=True):
        st.session_state.today_cursor+=timedelta(days=1); st.rerun()

shown_events=[e for e in all_events if e["date"]==shown_day]
if shown_events:
    inner='<div class="kicker">'+fmt_day(shown_day)+'</div>'+"".join(
        f'<div class="school">{e["school"]}</div><div class="people">{person_text(e["people"])}</div>' for e in shown_events)
    st.markdown(f'<section class="today">{inner}</section>',unsafe_allow_html=True)
else:
    msg="예정된 3차 점검이 없습니다"
    st.markdown(f'<section class="today empty"><div class="kicker">{fmt_day(shown_day)}</div><div class="school">{msg}</div><div class="people">좌우 화살표로 날짜를 이동하세요.</div></section>',unsafe_allow_html=True)

names=sorted({p for e in all_events for p in e["people"]})
selected=st.selectbox("내 이름",["전체 일정"]+names)
mine_only=st.toggle("내 일정만 보기",value=False,disabled=selected=="전체 일정")
events=[e for e in all_events if selected in e["people"]] if mine_only and selected!="전체 일정" else all_events

if "view" not in st.session_state or st.session_state.view not in ["주간","월간"]: st.session_state.view="주간"
st.segmented_control("보기",["주간","월간"],key="view",label_visibility="collapsed")

def cards(items):
    if not items:
        st.markdown('<div class="panel"><div class="none">예정된 3차 점검이 없습니다.</div></div>',unsafe_allow_html=True); return
    html='<div class="panel">'+"".join(
        f'<div class="event" style="border-left:4px solid {event_color(e)[0]};background:linear-gradient(90deg,{event_color(e)[1]},transparent 42%)"><div class="event-date">{fmt_day(e["date"])}</div><div class="event-school">{e["school"]}</div><div class="event-person" style="color:{event_color(e)[0]}">{person_text(e["people"])}</div></div>' for e in items)+'</div>'
    st.markdown(html,unsafe_allow_html=True)

if st.session_state.view=="주간":
    cursor=st.session_state.today_cursor
    start=cursor-timedelta(days=cursor.weekday()); end=start+timedelta(days=6)
    st.markdown(f'<div class="navtitle">{start.month}월 {start.day}일 – {end.month}월 {end.day}일</div>',unsafe_allow_html=True)
    cards([e for e in events if start<=e["date"]<=end])
else:
    cursor=st.session_state.month_cursor; y,m=cursor.year,cursor.month
    left,mid,right=st.columns([1,7,1],vertical_alignment="center")
    with left:
        if st.button("‹",key="month_prev",use_container_width=True):
            st.session_state.month_cursor=date(y-1,12,1) if m==1 else date(y,m-1,1); st.rerun()
    with mid: st.markdown(f'<div class="navtitle">{y}년 {m}월</div>',unsafe_allow_html=True)
    with right:
        if st.button("›",key="month_next",use_container_width=True):
            st.session_state.month_cursor=date(y+1,1,1) if m==12 else date(y,m+1,1); st.rerun()
    month_events=[e for e in events if (e["date"].year,e["date"].month)==(y,m)]
    by_day={}
    for e in month_events: by_day.setdefault(e["date"].day,[]).append(e)
    weeks=calendar.Calendar(firstweekday=0).monthdayscalendar(y,m)
    html='<div class="panel"><div class="cal">'+"".join(f'<div class="dow">{x}</div>' for x in ["월","화","수","목","금","토","일"])
    for week in weeks:
        for d in week:
            if not d: html+='<div class="cell blank"></div>'
            else:
                es=by_day.get(d,[])
                labels="".join(f'<div class="cal-school" style="color:{event_color(e)[0]};background:{event_color(e)[1]}">{month_label(e)}</div>' for e in es[:3])
                dot='<div class="dot"></div>' if es else ''
                html+=f'<div class="cell"><div class="num">{d}</div>{dot}{labels}</div>'
    html+='</div></div>'
    st.markdown(html,unsafe_allow_html=True)

if error: st.error("Notion 연결을 확인해주세요. Secrets와 데이터베이스 연결 권한이 필요합니다.")
elif not NOTION_TOKEN: st.info("Streamlit Cloud의 Secrets에 Notion 연결값을 등록하면 실제 일정이 표시됩니다.")
if st.button("↻ 최신 일정 불러오기",use_container_width=True):
    st.cache_data.clear(); st.rerun()
st.caption(f"마지막 확인 {datetime.now().strftime('%H:%M')}")

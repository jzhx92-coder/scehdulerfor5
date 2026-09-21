import calendar
from datetime import date, datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="자율형종합감사 일정", page_icon="📅", layout="centered")

NOTION_TOKEN = st.secrets.get("NOTION_TOKEN", "")
DATA_SOURCE_ID = st.secrets.get("NOTION_DATA_SOURCE_ID", "")


def clean_date(value):
    if not value:
        return None
    if isinstance(value, dict):
        value = value.get("start")
    value = str(value).strip().replace(". ", "-").replace(".", "-").strip("-")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def text_value(prop):
    if not isinstance(prop, dict):
        return str(prop or "")
    kind = prop.get("type")
    parts = prop.get(kind, []) if kind else []
    if kind == "date":
        return prop.get("date", {})
    if isinstance(parts, list):
        return "".join(x.get("plain_text", "") for x in parts)
    return str(parts or "")


@st.cache_data(ttl=60, show_spinner=False)
def load_events(token, source_id):
    if not token or not source_id:
        return []
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"https://api.notion.com/v1/data_sources/{source_id}/query",
        headers=headers,
        json={"page_size": 100},
        timeout=20,
    )
    response.raise_for_status()
    events = []
    for row in response.json().get("results", []):
        props = row.get("properties", {})
        raw_date = text_value(props.get("3차점검일", {}))
        event_date = clean_date(raw_date)
        if not event_date:
            title = text_value(props.get("3차점검일", {}))
            event_date = clean_date(title)
        school = text_value(props.get("학교명", {})).strip()
        people = [x.strip() for x in text_value(props.get("도감사관", {})).replace("/", ",").split(",") if x.strip()]
        if event_date and school:
            events.append({"date": event_date, "school": school, "people": people})
    return sorted(events, key=lambda x: (x["date"], x["school"]))


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
  .dayhead{font-size:1.12rem;font-weight:820;margin-bottom:.75rem}.event{position:relative;background:#f3f6fa;border:1px solid #edf0f5;border-radius:1.1rem;padding:.85rem 1rem .85rem 1.15rem;margin:.5rem 0}.event:before{content:"";position:absolute;left:0;top:.8rem;bottom:.8rem;width:4px;border-radius:0 4px 4px 0;background:#1677ff}.event-date{font-size:.78rem;color:#7f8a9a;font-weight:650}.event-school{font-size:1.03rem;font-weight:820;margin-top:.18rem}.event-person{font-size:.87rem;color:#657084;margin-top:.2rem}.none{text-align:center;color:#8a95a6;padding:2rem .5rem}
  .stButton button{border-radius:1rem;border:0;font-weight:750}
</style>
""", unsafe_allow_html=True)

today = date.today()
st.markdown('<div class="brand">자율형종합감사 일정</div>', unsafe_allow_html=True)
st.title(f"{today.month}월 {today.day}일")
st.markdown(f'<div class="sub">{today.strftime("%A")} · 오늘</div>', unsafe_allow_html=True)

try:
    events = load_events(NOTION_TOKEN, DATA_SOURCE_ID)
    error = None
except Exception as exc:
    events, error = [], str(exc)

today_events = [e for e in events if e["date"] == today]
if today_events:
    inner = '<div class="kicker">오늘의 일정</div>' + "".join(
        f'<div class="school">{e["school"]}</div><div class="people">도감사관 {" · ".join(e["people"])}</div>' for e in today_events
    )
    st.markdown(f'<section class="today">{inner}</section>', unsafe_allow_html=True)
else:
    st.markdown('<section class="today empty"><div class="kicker">오늘의 일정</div><div class="school">예정된 3차 점검이 없습니다</div><div class="people">다른 날짜의 일정은 아래에서 확인하세요.</div></section>', unsafe_allow_html=True)

names = sorted({p for e in events for p in e["people"]})
selected = st.selectbox("내 이름", ["전체 일정"] + names)
mine_only = st.toggle("내 일정만 보기", value=False, disabled=selected == "전체 일정")

if mine_only and selected != "전체 일정":
    events = [e for e in events if selected in e["people"]]

tab_today, tab_week, tab_month, tab_day = st.tabs(["오늘", "주간", "월간", "일간"])

def cards(items):
    if not items:
        st.markdown('<div class="panel"><div class="none">예정된 3차 점검이 없습니다.</div></div>', unsafe_allow_html=True)
        return
    html = '<div class="panel">' + "".join(
        f'<div class="event"><div class="event-date">{e["date"].strftime("%Y. %-m. %-d.")}</div><div class="event-school">{e["school"]}</div><div class="event-person">도감사관 {" · ".join(e["people"])}</div></div>' for e in items
    ) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

with tab_today:
    cards([e for e in events if e["date"] == today])
with tab_week:
    start = today - timedelta(days=today.weekday())
    cards([e for e in events if start <= e["date"] <= start + timedelta(days=6)])
with tab_month:
    month = st.date_input("확인할 달", today.replace(day=1), key="month")
    cards([e for e in events if (e["date"].year, e["date"].month) == (month.year, month.month)])
with tab_day:
    chosen = st.date_input("확인할 날짜", today, key="day")
    cards([e for e in events if e["date"] == chosen])

if error:
    st.error("Notion 연결을 확인해주세요. Secrets와 데이터베이스 연결 권한이 필요합니다.")
elif not NOTION_TOKEN:
    st.info("Streamlit Cloud의 Secrets에 Notion 연결값을 등록하면 실제 일정이 표시됩니다.")

if st.button("↻ 최신 일정 불러오기", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption(f"마지막 확인 {datetime.now().strftime('%H:%M')}")

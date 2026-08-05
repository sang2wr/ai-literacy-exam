import streamlit as st
import streamlit.components.v1 as components
import time
from utils.database import get_active_exam, create_exam, submit_exam, get_exam_by_id
from utils.questions import load_questions, ACTIVE_VERSION
from utils.theme import inject_base_css, navbar, font_scale_control, page_header, icon, info_pill, footer, logo_path, BRAND, render_html

st.set_page_config(
    page_title="시험 응시 | AI리터러시지도사",
    page_icon=logo_path("icon"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_base_css()

EXAM_MINUTES = 90
EXAM_SECONDS = EXAM_MINUTES * 60

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in") or not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 페이지로 이동")
    st.stop()

user = st.session_state.user
user_id = user["id"]

navbar(user)
font_scale_control()

# ── Check existing exam ───────────────────────────────────────────────────────
if "exam_id" in st.session_state:
    # Validate the exam still exists in DB (could have been deleted by admin)
    if not get_exam_by_id(st.session_state.exam_id):
        for k in ["exam_id", "exam_version", "exam_start_time", "answers", "exam_submitted", "mc_score"]:
            st.session_state.pop(k, None)

if "exam_id" not in st.session_state:
    existing = get_active_exam(user_id)
    if existing:
        st.session_state.exam_id = existing["id"]
        st.session_state.exam_version = existing.get("question_version") or ACTIVE_VERSION
        st.session_state.exam_start_time = (
            existing["started_at"]
            if isinstance(existing["started_at"], float)
            else time.time()  # fallback; will recalculate from DB if needed
        )

# ── Load questions (해당 응시자의 시험 버전 기준) ───────────────────────────────
areas = load_questions(st.session_state.get("exam_version"))

# ── Helper: compute remaining seconds ─────────────────────────────────────────
def get_remaining():
    start = st.session_state.get("exam_start_time", time.time())
    elapsed = time.time() - start
    return max(0, EXAM_SECONDS - elapsed)

# ── Pre-exam screen ───────────────────────────────────────────────────────────
def show_pre_exam():
    page_header("AI리터러시지도사 자격시험", "응시 전 안내 사항을 확인해주세요", "pencil")

    render_html(f"""
    <div class="sw-info-strip">
        {info_pill("book-open", "총 문항", "80문제")}
        {info_pill("clock", "제한 시간", "90분")}
        {info_pill("list-checks", "객관식", "분야별 18문제")}
        {info_pill("file-text", "주관식", "분야별 2문제")}
    </div>
    """)

    areas_preview = ["AI 개념 이해", "AI와 문제해결", "AI 도구 및 플랫폼 사용", "지도 계획안 작성"]
    area_html = "".join(
        f'<div class="sw-info-pill"><div class="ic">{icon("grid", 16)}</div>'
        f'<div class="txt"><b>분야 {i+1}</b><span>{name}</span></div></div>'
        for i, name in enumerate(areas_preview)
    )
    render_html(f"""
    <div class="sw-card">
        <p style="font-weight:800;color:{BRAND['ink']};margin:0 0 12px 0;">
            {icon("layers", 18, BRAND['coral'])} 분야 구성
        </p>
        <div class="sw-info-strip" style="margin:0;">{area_html}</div>
    </div>
    """)

    st.warning("시험 시작 후에는 중간에 나가도 진행 중 상태가 유지됩니다. 시간이 초과되면 자동으로 제출됩니다.")

    # Check if already has a submitted exam
    from utils.database import get_user_exams
    past = [e for e in get_user_exams(user_id) if e["status"] != "in_progress"]
    if past:
        st.info("이미 시험을 제출한 기록이 있습니다. 새로 시작하면 기존 기록은 유지됩니다.")

    if st.button("시험 시작하기", type="primary", use_container_width=True):
        with st.spinner("시험을 준비하는 중..."):
            exam = create_exam(user_id)
        st.session_state.exam_id = exam["id"]
        st.session_state.exam_version = exam.get("question_version") or ACTIVE_VERSION
        st.session_state.exam_start_time = time.time()
        st.session_state.answers = {}  # {question_id: answer}
        st.rerun()

# ── Timer HTML component ───────────────────────────────────────────────────────
def render_timer(deadline_epoch: float):
    timer_html = f"""
    <div id="timer-box" style="
        background: {BRAND['ink']}; color: #fff;
        padding: 16px 24px; border-radius: 14px;
        font-family: 'Pretendard', monospace; font-size: 1.7rem; font-weight: 800;
        text-align: center; user-select: none; box-shadow: 0 6px 16px rgba(20,18,18,0.18);
    ">
        남은 시간&nbsp; <span id="t">--:--</span>
    </div>
    <script>
      (function() {{
        var deadline = {deadline_epoch * 1000};
        function tick() {{
          var now = Date.now();
          var rem = Math.max(0, deadline - now);
          var m = Math.floor(rem / 60000);
          var s = Math.floor((rem % 60000) / 1000);
          var el = document.getElementById('t');
          if (!el) return;
          el.textContent = String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
          if (rem <= 300000) document.getElementById('timer-box').style.background = '{BRAND['coral']}';
          if (rem > 0) setTimeout(tick, 1000);
          else el.textContent = '00:00 시간 초과!';
        }}
        tick();
      }})();
    </script>
    """
    components.html(timer_html, height=88)

# ── Auto-submit logic ─────────────────────────────────────────────────────────
def do_submit(auto: bool = False):
    answers_state = st.session_state.get("answers", {})
    mc_score = 0
    answer_rows = []

    for area in areas:
        area_id = area["area_id"]
        for q in area["questions"]:
            qid = q["id"]
            user_ans = answers_state.get(qid, "")
            correct = None
            if q["type"] == "mc":
                correct = (str(user_ans) == str(q.get("correct", -1)))
                if correct:
                    mc_score += 1
            answer_rows.append({
                "exam_id": st.session_state.exam_id,
                "question_id": qid,
                "area_id": area_id,
                "answer_text": str(user_ans) if user_ans != "" else None,
                "is_correct": correct,
            })

    ok = submit_exam(st.session_state.exam_id, answer_rows, mc_score)
    if ok:
        st.session_state.exam_submitted = True
        st.session_state.mc_score = mc_score
        if auto:
            st.session_state.auto_submitted = True
        # Clean up exam session
        for k in ["exam_id", "exam_version", "exam_start_time", "answers"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Exam submitted screen ─────────────────────────────────────────────────────
if st.session_state.get("exam_submitted"):
    auto = st.session_state.pop("auto_submitted", False)
    score = st.session_state.pop("mc_score", 0)
    page_header("시험 제출 완료", "수고하셨습니다! 채점 결과는 내 결과 페이지에서 확인할 수 있습니다.", "check-circle")
    if auto:
        st.warning("⏱ 시간이 초과되어 자동으로 제출되었습니다.")
    else:
        st.success("시험이 성공적으로 제출되었습니다!")
    st.metric("객관식 자동 채점 점수", f"{score}점 / 72점")
    st.info("주관식 및 실기 점수는 관리자가 채점 후 반영됩니다.")
    st.page_link("pages/2_results.py", label="내 결과 보기")
    st.stop()

# ── Pre-exam ──────────────────────────────────────────────────────────────────
if "exam_id" not in st.session_state:
    show_pre_exam()
    st.stop()

# ── Exam in progress ──────────────────────────────────────────────────────────
# Auto-refresh every 60 seconds to catch time expiry server-side
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60_000, key="exam_autorefresh")

remaining = get_remaining()
if remaining <= 0:
    st.warning("⏱ 시간이 초과되었습니다. 자동 제출 중...")
    do_submit(auto=True)
    st.stop()

deadline = st.session_state.exam_start_time + EXAM_SECONDS

# Initialize answers dict
if "answers" not in st.session_state:
    st.session_state.answers = {}

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_timer = st.columns([3, 1])
with col_title:
    page_header("AI리터러시지도사 자격시험", "분야별 탭을 이동하며 응시하세요", "pencil")
with col_timer:
    render_timer(deadline)

st.divider()

# ── Tab CSS (브랜드 컬러 + 고령 응시자를 위한 글자 크기 확대) ─────────────────
render_html(f"""
<style>
/* 탭 버튼 기본 */
[data-testid="stTab"] {{
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    padding: 14px 22px !important;
    border-radius: 12px 12px 0 0 !important;
    background: {BRAND['card']} !important;
    color: {BRAND['muted']} !important;
    border: 1.5px solid {BRAND['border']} !important;
    border-bottom: none !important;
    margin-right: 8px !important;
    transition: all 0.2s !important;
}}
[data-testid="stTab"]:hover {{
    color: {BRAND['coral']} !important;
}}
[data-testid="stTab"][aria-selected="true"] {{
    background: {BRAND['coral']} !important;
    color: #ffffff !important;
    border-color: transparent !important;
    box-shadow: 0 -4px 14px rgba(241,88,53,0.25) !important;
}}
[role="tablist"] {{
    background: transparent !important;
    gap: 4px !important;
    border-bottom: 2px solid {BRAND['border']} !important;
    padding-bottom: 0 !important;
    flex-wrap: wrap !important;
    row-gap: 8px !important;
}}
[data-testid="stTab"] {{
    white-space: normal !important;
}}
[data-testid="stTab"] p {{
    white-space: normal !important;
    word-break: keep-all !important;
}}

/* 고령 응시자를 위한 글자 크기 확대 */
[data-testid="stMarkdownContainer"] p {{
    font-size: 1.22rem !important;
    line-height: 1.75 !important;
}}
.stRadio p, .stRadio label {{
    font-size: 1.16rem !important;
    line-height: 1.65 !important;
}}
[data-testid="stCaptionContainer"] p, .stCaptionContainer p {{
    font-size: 1.05rem !important;
}}
.stButton > button {{
    font-size: 1.15rem !important;
    padding: 0.8rem 1.1rem !important;
}}
textarea {{
    font-size: 1.12rem !important;
}}
</style>
""")

# ── Question tabs ─────────────────────────────────────────────────────────────
tabs = st.tabs([f"분야{a['area_id']} {a['area_name']}" for a in areas])

# 탭 클릭 시 스크롤 최상단 이동
components.html("""
<script>
(function() {
    function getTopDoc() {
        var candidates = [];
        try { candidates.push(window.parent.document); } catch (e) {}
        try { candidates.push(window.top.document); } catch (e) {}
        for (var i = 0; i < candidates.length; i++) {
            if (candidates[i] && candidates[i].querySelector('[data-testid="stTab"]')) return candidates[i];
        }
        return candidates[0] || document;
    }

    function scrollToTop() {
        var doc = getTopDoc();
        var selectors = [
            '[data-testid="stAppViewContainer"]',
            '[data-testid="stMain"]',
            '.main',
            'section.main'
        ];
        selectors.forEach(function(sel) {
            var el = doc.querySelector(sel);
            if (el) el.scrollTop = 0;
        });
        doc.documentElement.scrollTop = 0;
        doc.body.scrollTop = 0;
    }

    function attach() {
        var tabs = getTopDoc().querySelectorAll('[data-testid="stTab"]');
        tabs.forEach(function(t) {
            if (!t._scrollTop) {
                t._scrollTop = true;
                t.addEventListener('click', function() {
                    setTimeout(scrollToTop, 150);
                });
            }
        });
    }
    attach();
    setTimeout(attach, 500);
    setTimeout(attach, 1200);
})();
</script>
""", height=0)

for tab, area in zip(tabs, areas):
    with tab:
        area_id = area["area_id"]
        st.subheader(f"분야 {area_id}: {area['area_name']}")
        mc_qs = [q for q in area["questions"] if q["type"] == "mc"]
        sa_qs = [q for q in area["questions"] if q["type"] == "sa"]

        st.markdown("#### 객관식 문제")
        for q in mc_qs:
            qid = q["id"]
            current = st.session_state.answers.get(qid, None)
            idx = current if isinstance(current, int) and 0 <= current < 4 else None
            choice = st.radio(
                f"**{qid}번. {q['text']}**",
                options=list(range(4)),
                format_func=lambda i, opts=q["options"]: f"{'①②③④'[i]} {opts[i]}",
                index=idx,
                key=f"mc_{qid}",
            )
            st.session_state.answers[qid] = choice
            st.divider()

        st.markdown("#### 주관식 문제")
        for q in sa_qs:
            qid = q["id"]
            current = st.session_state.answers.get(qid, "")
            answer = st.text_area(
                f"**{qid}번. {q['text']}**",
                value=current,
                height=130,
                key=f"sa_{qid}",
                placeholder="답안을 입력하세요.",
            )
            st.session_state.answers[qid] = answer
            st.divider()

# ── Progress summary ──────────────────────────────────────────────────────────
st.markdown("---")
total_answered = sum(
    1 for area in areas for q in area["questions"]
    if st.session_state.answers.get(q["id"]) not in [None, ""]
)
st.caption(f"응답 완료: {total_answered} / 80문제")
st.progress(total_answered / 80)

# ── 분야별 이동 탭 (최종 제출 위) ─────────────────────────────────────────────
area_btns_html = ""
for i, area in enumerate(areas):
    qs = area["questions"]
    answered = sum(1 for q in qs if st.session_state.answers.get(q["id"]) not in [None, ""])
    total_q = len(qs)
    done = answered == total_q
    bg = BRAND['coral'] if done else BRAND['card']
    border = "transparent" if done else BRAND['border']
    color = "#fff" if done else BRAND['ink']
    sub_color = "rgba(255,255,255,0.8)" if done else BRAND['muted']
    status_mark = icon("check-circle", 17, "#fff") + " " if done else ""
    area_btns_html += f"""
    <button onclick="goToArea({i})" style="
        background:{bg}; color:{color}; border:1.5px solid {border};
        padding:20px 12px; border-radius:14px; cursor:pointer;
        font-size:1.15rem; font-weight:700; width:100%;
        box-shadow:{'0 6px 16px rgba(241,88,53,0.28)' if done else '0 1px 2px rgba(20,18,18,0.04)'}; transition:filter 0.2s, transform 0.15s;
        line-height:1.65; font-family:'Pretendard', sans-serif;
    " onmouseover="this.style.filter='brightness(0.97)';this.style.transform='translateY(-1px)'" onmouseout="this.style.filter='none';this.style.transform='none'">
        {status_mark}분야 {i+1}<br>
        <span style="font-size:1rem;font-weight:600">{area['area_name']}</span><br>
        <span style="font-size:0.95rem;color:{sub_color}">{answered}/{total_q} 응답</span>
    </button>"""

nav_html = f"""
<div style="margin:8px 0 20px 0;">
    <div style="
        background:{BRAND['card']}; border:1px solid {BRAND['border']};
        border-radius:18px; padding:22px; margin-bottom:4px;
        box-shadow:0 2px 4px rgba(20,18,18,0.03), 0 8px 20px rgba(20,18,18,0.04);
    ">
        <p style="color:{BRAND['ink']};font-weight:800;font-size:1.15rem;margin:0 0 16px 0;">
            분야별 바로 이동
        </p>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:14px;">
            {area_btns_html}
        </div>
    </div>
</div>
<script>
function resizeFrame() {{
    try {{
        if (window.frameElement) {{
            window.frameElement.style.height = (document.body.scrollHeight + 24) + 'px';
        }}
    }} catch (e) {{}}
}}
window.addEventListener('load', resizeFrame);
window.addEventListener('resize', resizeFrame);
setTimeout(resizeFrame, 100);
setTimeout(resizeFrame, 400);

function getTopDoc() {{
    var candidates = [];
    try {{ candidates.push(window.parent.document); }} catch (e) {{}}
    try {{ candidates.push(window.top.document); }} catch (e) {{}}
    for (var i = 0; i < candidates.length; i++) {{
        if (candidates[i] && candidates[i].querySelector('[data-testid="stTab"]')) return candidates[i];
    }}
    return candidates[0] || document;
}}
function scrollToTop() {{
    var doc = getTopDoc();
    ['[data-testid="stAppViewContainer"]','[data-testid="stMain"]','.main','section.main'].forEach(function(sel) {{
        var el = doc.querySelector(sel);
        if (el) el.scrollTop = 0;
    }});
    doc.documentElement.scrollTop = 0;
    doc.body.scrollTop = 0;
}}
function goToArea(idx) {{
    var tabs = getTopDoc().querySelectorAll('[data-testid="stTab"]');
    if (tabs && tabs[idx]) {{
        tabs[idx].click();
        setTimeout(scrollToTop, 150);
    }}
}}
</script>
"""
components.html(nav_html, height=230)

# ── Submit button ─────────────────────────────────────────────────────────────
st.markdown("### 최종 제출")
st.warning("제출 후에는 수정이 불가능합니다. 모든 문제에 답했는지 확인 후 제출하세요.")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("최종 제출", type="primary", use_container_width=True):
        st.session_state.confirm_submit = True

if st.session_state.get("confirm_submit"):
    st.error("정말로 제출하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("예, 제출합니다", type="primary", use_container_width=True):
            st.session_state.confirm_submit = False
            do_submit(auto=False)
    with c2:
        if st.button("취소", use_container_width=True):
            st.session_state.confirm_submit = False
            st.rerun()

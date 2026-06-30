import streamlit as st
import streamlit.components.v1 as components
import json
import time
from pathlib import Path
from utils.database import get_active_exam, create_exam, submit_exam

st.set_page_config(
    page_title="시험 응시 | AI리터러시지도사",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

EXAM_MINUTES = 80
EXAM_SECONDS = EXAM_MINUTES * 60

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in") or not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 페이지로 이동")
    st.stop()

if st.session_state.user.get("is_admin"):
    st.warning("관리자 계정으로는 시험을 응시할 수 없습니다.")
    st.stop()

user = st.session_state.user
user_id = user["id"]

# ── Load questions ────────────────────────────────────────────────────────────
@st.cache_data
def load_questions():
    path = Path(__file__).parent.parent / "data" / "questions.json"
    return json.loads(path.read_text(encoding="utf-8"))

areas = load_questions()

# ── Check existing exam ───────────────────────────────────────────────────────
if "exam_id" not in st.session_state:
    existing = get_active_exam(user_id)
    if existing:
        st.session_state.exam_id = existing["id"]
        st.session_state.exam_start_time = (
            existing["started_at"]
            if isinstance(existing["started_at"], float)
            else time.time()  # fallback; will recalculate from DB if needed
        )

# ── Helper: compute remaining seconds ─────────────────────────────────────────
def get_remaining():
    start = st.session_state.get("exam_start_time", time.time())
    elapsed = time.time() - start
    return max(0, EXAM_SECONDS - elapsed)

# ── Pre-exam screen ───────────────────────────────────────────────────────────
def show_pre_exam():
    st.title("✏️ AI리터러시지도사 자격시험")
    st.markdown(f"""
    ### 시험 안내
    | 항목 | 내용 |
    |---|---|
    | 총 문항 수 | **80문제** (4개 분야 × 20문제) |
    | 객관식 | 각 분야 18문제 (4지선다) |
    | 주관식 | 각 분야 2문제 (단답형) |
    | 제한 시간 | **80분** |
    | 시험 방식 | 시간 초과 시 자동 제출 |

    ### 분야 구성
    1. AI 개념 이해
    2. AI와 문제해결
    3. AI 도구 및 플랫폼 사용
    4. 지도 계획안 작성

    > ⚠️ 시험 시작 후에는 중간에 나가도 진행 중 상태가 유지됩니다.
    > 시간이 초과되면 자동으로 제출됩니다.
    """)

    # Check if already has a submitted exam
    from utils.database import get_user_exams
    past = [e for e in get_user_exams(user_id) if e["status"] != "in_progress"]
    if past:
        st.warning("이미 시험을 제출한 기록이 있습니다. 새로 시작하면 기존 기록은 유지됩니다.")

    if st.button("🚀 시험 시작하기", type="primary", use_container_width=True):
        with st.spinner("시험을 준비하는 중..."):
            exam = create_exam(user_id)
        st.session_state.exam_id = exam["id"]
        st.session_state.exam_start_time = time.time()
        st.session_state.answers = {}  # {question_id: answer}
        st.rerun()

# ── Timer HTML component ───────────────────────────────────────────────────────
def render_timer(deadline_epoch: float):
    timer_html = f"""
    <div id="timer-box" style="
        background: #1e1e2e; color: white;
        padding: 12px 24px; border-radius: 10px;
        font-family: monospace; font-size: 1.6rem;
        text-align: center; user-select: none;
    ">
        ⏱ 남은 시간: <span id="t">--:--</span>
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
          if (rem <= 300000) document.getElementById('timer-box').style.color = '#ff4444';
          if (rem > 0) setTimeout(tick, 1000);
          else el.textContent = '00:00 ⚠ 시간 초과!';
        }}
        tick();
      }})();
    </script>
    """
    components.html(timer_html, height=70)

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
        for k in ["exam_id", "exam_start_time", "answers"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Exam submitted screen ─────────────────────────────────────────────────────
if st.session_state.get("exam_submitted"):
    auto = st.session_state.pop("auto_submitted", False)
    score = st.session_state.pop("mc_score", 0)
    st.title("✅ 시험 제출 완료")
    if auto:
        st.warning("⏱ 시간이 초과되어 자동으로 제출되었습니다.")
    else:
        st.success("시험이 성공적으로 제출되었습니다!")
    st.metric("객관식 자동 채점 점수", f"{score}점 / 72점")
    st.info("주관식 및 실기 점수는 관리자가 채점 후 반영됩니다.")
    st.page_link("pages/2_내결과.py", label="📋 내 결과 보기")
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
    st.title("✏️ AI리터러시지도사 자격시험")
with col_timer:
    render_timer(deadline)

st.divider()

# ── Question tabs ─────────────────────────────────────────────────────────────
tabs = st.tabs([f"📚 {a['area_name']}" for a in areas])

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
                f"**{qid}번.** {q['text']}",
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
                f"**{qid}번.** {q['text']}",
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
st.caption(f"📝 응답 완료: {total_answered} / 80문제")
st.progress(total_answered / 80)

# ── Submit button ─────────────────────────────────────────────────────────────
st.markdown("### 최종 제출")
st.warning("제출 후에는 수정이 불가능합니다. 모든 문제에 답했는지 확인 후 제출하세요.")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📤 최종 제출", type="primary", use_container_width=True):
        st.session_state.confirm_submit = True

if st.session_state.get("confirm_submit"):
    st.error("정말로 제출하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 예, 제출합니다", type="primary", use_container_width=True):
            st.session_state.confirm_submit = False
            do_submit(auto=False)
    with c2:
        if st.button("❌ 취소", use_container_width=True):
            st.session_state.confirm_submit = False
            st.rerun()

import streamlit as st
from utils.database import get_user_exams, get_exam_answers
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="내 결과 | AI리터러시지도사",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not st.session_state.get("logged_in") or not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 페이지로 이동")
    st.stop()

user = st.session_state.user
user_id = user["id"]


@st.cache_data
def load_questions():
    path = Path(__file__).parent.parent / "data" / "questions.json"
    return json.loads(path.read_text(encoding="utf-8"))

areas = load_questions()
q_map = {q["id"]: q for area in areas for q in area["questions"]}

# ── Page ──────────────────────────────────────────────────────────────────────
st.title("📋 내 시험 결과")
st.caption(f"{user['name']}님의 시험 기록")

exams = get_user_exams(user_id)
submitted = [e for e in exams if e["status"] in ("submitted", "graded")]

if not submitted:
    st.info("아직 제출된 시험 기록이 없습니다.")
    st.page_link("pages/1_시험보기.py", label="✏️ 시험 응시하러 가기")
    st.stop()

for exam in submitted:
    status_label = {"submitted": "채점 대기 중", "graded": "채점 완료"}.get(exam["status"], exam["status"])
    submitted_at = exam.get("submitted_at", "")
    if submitted_at:
        try:
            dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
            submitted_at = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    with st.expander(f"📄 시험 결과 — {submitted_at}  |  상태: {status_label}", expanded=True):
        mc = exam.get("mc_score", 0) or 0
        sa = exam.get("sa_score") or 0
        practical = exam.get("practical_score")
        p_result = exam.get("practical_result", "")
        p_notes = exam.get("practical_notes", "")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("객관식 점수", f"{mc} / 72점")
        col2.metric("주관식 점수", f"{sa} / 16점" if exam["status"] == "graded" else "채점 전")
        if exam["status"] == "graded":
            col3.metric("실기 점수", f"{practical}점" if practical is not None else "-")
            col4.metric("실기 결과", p_result or "-")
        else:
            col3.metric("실기 점수", "채점 전")
            col4.metric("실기 결과", "채점 전")

        if exam["status"] == "graded" and p_notes:
            st.info(f"📝 강사 코멘트: {p_notes}")

        # Show written exam answers
        if st.checkbox("📖 내 답안 보기", key=f"show_{exam['id']}"):
            answers = get_exam_answers(exam["id"])
            ans_map = {a["question_id"]: a for a in answers}

            for area in areas:
                st.markdown(f"#### {area['area_name']}")
                for q in area["questions"]:
                    qid = q["id"]
                    ans_row = ans_map.get(qid)
                    if q["type"] == "mc":
                        user_idx = ans_row["answer_text"] if ans_row else None
                        correct_idx = str(q.get("correct", -1))
                        is_correct = ans_row["is_correct"] if ans_row else False
                        icon = "✅" if is_correct else "❌"
                        try:
                            user_text = q["options"][int(user_idx)] if user_idx is not None else "미응답"
                        except Exception:
                            user_text = "미응답"
                        correct_text = q["options"][q["correct"]]
                        st.markdown(
                            f"{icon} **{qid}번** {q['text']}  \n"
                            f"내 답: {user_text}  \n"
                            f"{'정답: ' + correct_text if not is_correct else ''}"
                        )
                    else:
                        user_ans = ans_row["answer_text"] if ans_row else "미응답"
                        st.markdown(
                            f"📝 **{qid}번** {q['text']}  \n"
                            f"내 답안: {user_ans or '미응답'}"
                        )
                st.divider()

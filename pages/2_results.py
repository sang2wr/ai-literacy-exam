import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from utils.database import get_user_exams, get_exam_answers, get_area_mc_scores, calculate_written_result

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
    st.page_link("pages/1_exam.py", label="✏️ 시험 응시하러 가기")
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
        mc_correct_total = exam.get("mc_score", 0) or 0
        practical = exam.get("practical_score")
        p_result = exam.get("practical_result", "")
        p_notes = exam.get("practical_notes", "")
        written_result = exam.get("written_result") or ""

        # ── 합격 판정 배너 ──────────────────────────────────────────────────
        if exam["status"] == "graded":
            if p_result == "합격" and written_result == "합격":
                st.success("🎉 최종 합격! 필기 합격 + 실기 합격")
            elif written_result == "합격" and not p_result:
                st.info("✅ 필기 합격 — 실기 시험 대상자입니다.")
            elif written_result == "탈락":
                st.error("❌ 필기 불합격")
            elif p_result == "불합격":
                st.error("❌ 실기 불합격")
        else:
            st.warning("⏳ 채점 대기 중 — 주관식 채점 후 합격 여부가 확정됩니다.")

        # ── 필기 점수 요약 ───────────────────────────────────────────────────
        st.markdown("#### 📊 필기시험 점수")

        # Per-area breakdown
        area_mc = get_area_mc_scores(exam["id"])
        try:
            area_sa = {int(k): v for k, v in json.loads(exam.get("sa_scores") or "{}").items()}
        except Exception:
            area_sa = {}

        area_cols = st.columns(4)
        area_totals = {}
        for i, area in enumerate(areas):
            aid = area["area_id"]
            mc_pts = area_mc.get(aid, 0) * 5
            sa_pts = area_sa.get(aid, 0)
            total_pts = mc_pts + sa_pts
            area_totals[aid] = total_pts
            pass_mark = "✅" if total_pts >= 50 else "❌"
            with area_cols[i]:
                st.metric(
                    f"분야{aid} {pass_mark}",
                    f"{total_pts}점 / 100점",
                    f"MC {mc_pts}pt + SA {sa_pts}pt" if area_sa else f"MC {mc_pts}pt",
                )

        if area_totals:
            avg = sum(area_totals.values()) / 4
            c1, c2, c3 = st.columns(3)
            c1.metric("필기 평균", f"{avg:.1f}점")
            c2.metric("필기 합격 기준", "평균 60점 이상 & 분야별 50점 이상")
            c3.metric("필기 결과", written_result or ("채점 전" if exam["status"] != "graded" else "-"))
        else:
            st.caption(f"객관식 정답 수: {mc_correct_total} / 72문제 ({mc_correct_total * 5}점 / 360점)")

        # ── 실기 점수 ────────────────────────────────────────────────────────
        if exam["status"] == "graded":
            st.markdown("#### 🎤 실기시험")
            if written_result == "합격":
                col1, col2 = st.columns(2)
                col1.metric("실기 점수", f"{practical}점" if practical is not None else "-")
                col2.metric("실기 결과", p_result or "-")
                if p_notes:
                    st.info(f"📝 강사 코멘트: {p_notes}")
            else:
                st.caption("필기 불합격으로 실기 시험 대상이 아닙니다.")

        # ── 내 답안 보기 ─────────────────────────────────────────────────────
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

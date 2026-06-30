import streamlit as st
import pandas as pd
from utils.database import get_all_exams_with_users, get_exam_answers, update_practical_score
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="관리자 패널 | AI리터러시지도사",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in") or not st.session_state.get("user"):
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 페이지로 이동")
    st.stop()

if not st.session_state.user.get("is_admin"):
    st.error("관리자만 접근할 수 있습니다.")
    st.stop()


@st.cache_data
def load_questions():
    path = Path(__file__).parent.parent / "data" / "questions.json"
    return json.loads(path.read_text(encoding="utf-8"))

areas = load_questions()
q_map = {q["id"]: q for area in areas for q in area["questions"]}

# ── Page ──────────────────────────────────────────────────────────────────────
st.title("📊 관리자 패널")
st.caption("시험 결과 관리 및 점수 입력")

tab1, tab2, tab3 = st.tabs(["📋 전체 결과 목록", "✏️ 점수 입력 / 채점", "📝 정답표"])

# ── Tab 1: Summary table ──────────────────────────────────────────────────────
with tab1:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

    exams = get_all_exams_with_users()
    if not exams:
        st.info("제출된 시험이 없습니다.")
    else:
        rows = []
        for e in exams:
            u = e.get("users") or {}
            submitted_at = e.get("submitted_at", "")
            try:
                dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
                submitted_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            rows.append({
                "ID": e["id"][:8] + "...",
                "이름": u.get("name", "-"),
                "이메일": u.get("email", "-"),
                "연락처": u.get("phone", "-"),
                "제출일시": submitted_at,
                "상태": {"submitted": "채점 대기", "graded": "채점 완료"}.get(e["status"], e["status"]),
                "객관식": e.get("mc_score", 0),
                "주관식": e.get("sa_score", "-"),
                "실기점수": e.get("practical_score", "-"),
                "실기결과": e.get("practical_result", "-"),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 CSV 다운로드",
            data=csv,
            file_name="시험결과.csv",
            mime="text/csv",
        )

# ── Tab 2: Grade individual exam ──────────────────────────────────────────────
with tab2:
    exams_all = get_all_exams_with_users()
    if not exams_all:
        st.info("채점할 시험이 없습니다.")
        st.stop()

    # Selector
    options = {}
    for e in exams_all:
        u = e.get("users") or {}
        label = f"{u.get('name','?')} ({u.get('email','?')})  —  {e.get('submitted_at','')[:16]}  [{e['status']}]"
        options[label] = e

    selected_label = st.selectbox("채점할 응시자 선택", list(options.keys()))
    exam = options[selected_label]

    st.divider()

    # Load answers
    answers = get_exam_answers(exam["id"])
    ans_map = {a["question_id"]: a for a in answers}
    u = exam.get("users") or {}

    col1, col2, col3 = st.columns(3)
    col1.metric("응시자", u.get("name", "-"))
    col2.metric("객관식 자동점수", f"{exam.get('mc_score', 0)} / 72점")
    col3.metric("현재 상태", {"submitted": "채점 대기", "graded": "채점 완료"}.get(exam["status"], exam["status"]))

    # Show short-answer questions for manual review
    st.markdown("### 📝 주관식 답안 검토")
    sa_qs = [q for area in areas for q in area["questions"] if q["type"] == "sa"]
    for q in sa_qs:
        qid = q["id"]
        area_name = next((a["area_name"] for a in areas for aq in a["questions"] if aq["id"] == qid), "")
        ans_row = ans_map.get(qid)
        user_ans = ans_row["answer_text"] if ans_row else "미응답"
        with st.container():
            st.markdown(f"**{qid}번 [{area_name}]** {q['text']}")
            st.text_area(
                "응시자 답안",
                value=user_ans or "미응답",
                height=100,
                disabled=True,
                key=f"sa_view_{qid}",
            )
        st.divider()

    # Scoring form
    st.markdown("### 🎯 점수 입력")
    with st.form(f"score_form_{exam['id']}"):
        sa_score = st.number_input(
            "주관식 점수 (0~16점)",
            min_value=0, max_value=16,
            value=exam.get("sa_score") or 0,
            step=1,
        )
        practical_score = st.number_input(
            "실기 점수",
            min_value=0, max_value=100,
            value=exam.get("practical_score") or 0,
            step=1,
        )
        practical_result = st.selectbox(
            "실기 결과",
            ["", "합격", "불합격"],
            index=["", "합격", "불합격"].index(exam.get("practical_result") or ""),
        )
        practical_notes = st.text_area(
            "강사 코멘트 (선택)",
            value=exam.get("practical_notes") or "",
            height=80,
        )
        save = st.form_submit_button("💾 저장", type="primary", use_container_width=True)

    if save:
        ok = update_practical_score(
            exam["id"],
            int(practical_score),
            practical_result,
            practical_notes,
            int(sa_score),
        )
        if ok:
            st.success("저장되었습니다!")
            st.cache_data.clear()
        else:
            st.error("저장 중 오류가 발생했습니다.")

# ── Tab 3: 정답표 ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 📝 객관식 정답표")
    st.caption("객관식 72문제 정답 목록입니다. 주관식은 관리자가 직접 채점합니다.")

    for area in areas:
        mc_qs = [q for q in area["questions"] if q["type"] == "mc"]
        sa_qs = [q for q in area["questions"] if q["type"] == "sa"]

        with st.expander(f"📚 분야 {area['area_id']}: {area['area_name']}  ({len(mc_qs)}문항)", expanded=False):
            # MC 정답표
            rows = []
            for q in mc_qs:
                correct_idx = q.get("correct", 0)
                correct_text = q["options"][correct_idx]
                num = "①②③④"[correct_idx]
                rows.append({
                    "번호": q["id"],
                    "문제": q["text"][:40] + ("..." if len(q["text"]) > 40 else ""),
                    "정답": f"{num} {correct_text}",
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # SA 문제
            st.markdown("**주관식 문제**")
            for q in sa_qs:
                with st.container(border=True):
                    st.markdown(f"**{q['id']}번.** {q['text']}")
                    answer = q.get("answer", "")
                    if answer:
                        st.success(f"✅ 정답/예시: {answer}")
                    else:
                        st.caption("수동 채점")

    # 전체 정답 CSV 다운로드
    st.divider()
    all_rows = []
    for area in areas:
        for q in area["questions"]:
            if q["type"] == "mc":
                correct_idx = q.get("correct", 0)
                all_rows.append({
                    "분야": area["area_name"],
                    "번호": q["id"],
                    "유형": "객관식",
                    "문제": q["text"],
                    "정답번호": correct_idx + 1,
                    "정답내용": q["options"][correct_idx],
                })
            else:
                all_rows.append({
                    "분야": area["area_name"],
                    "번호": q["id"],
                    "유형": "주관식",
                    "문제": q["text"],
                    "정답번호": "-",
                    "정답내용": q.get("answer", "수동 채점"),
                })
    csv = pd.DataFrame(all_rows).to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "📥 전체 정답표 CSV 다운로드",
        data=csv,
        file_name="정답표.csv",
        mime="text/csv",
    )

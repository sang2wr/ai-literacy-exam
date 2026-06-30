import streamlit as st
import pandas as pd
from utils.database import (
    get_all_exams_with_users, get_exam_answers, update_practical_score,
    delete_exam, get_area_mc_scores, calculate_written_result,
)
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
    col_refresh, col_info = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()

    exams = get_all_exams_with_users()
    if not exams:
        st.info("제출된 시험이 없습니다.")
    else:
        # ── 요약 테이블 ───────────────────────────────────────────────────────
        rows = []
        for e in exams:
            u = e.get("users") or {}
            submitted_at = e.get("submitted_at", "")
            try:
                dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
                submitted_at = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            mc_pts = (e.get("mc_score") or 0) * 5
            sa_pts = e.get("sa_score") or 0
            written = e.get("written_result") or "-"
            p_result = e.get("practical_result") or "-"
            final = "최종합격" if (written == "합격" and p_result == "합격") else (
                "필기합격(실기대상)" if written == "합격" else (
                    "탈락" if written == "탈락" else "-"
                )
            )
            rows.append({
                "ID": e["id"][:8] + "...",
                "이름": u.get("name", "-"),
                "이메일": u.get("email", "-"),
                "연락처": u.get("phone", "-"),
                "제출일시": submitted_at,
                "상태": {"submitted": "채점 대기", "graded": "채점 완료"}.get(e["status"], e["status"]),
                "MC(점)": mc_pts,
                "SA(점)": sa_pts,
                "필기결과": written,
                "실기점수": e.get("practical_score") or "-",
                "실기결과": p_result,
                "최종결과": final,
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

        # ── 기록 삭제 ──────────────────────────────────────────────────────
        st.divider()
        st.markdown("### 🗑 기록 삭제 (재시험 허용)")
        st.caption("삭제 후에는 응시자가 다시 시험을 볼 수 있습니다. 삭제된 기록은 복구할 수 없습니다.")

        for e in exams:
            u = e.get("users") or {}
            name = u.get("name", "-")
            email = u.get("email", "-")
            submitted_at = e.get("submitted_at", "")[:16]
            exam_id = e["id"]
            status_label = {"submitted": "채점 대기", "graded": "채점 완료"}.get(e["status"], e["status"])

            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{name}** ({email}) | {submitted_at} | {status_label} | 객관식 {e.get('mc_score', 0)}점")
            with col_btn:
                if st.button("🗑 삭제", key=f"del_{exam_id}"):
                    st.session_state[f"confirm_del_{exam_id}"] = True

            if st.session_state.get(f"confirm_del_{exam_id}"):
                st.warning(f"⚠️ **{name}**님의 시험 기록을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ 삭제 확인", key=f"confirm_yes_{exam_id}", type="primary"):
                        if delete_exam(exam_id):
                            st.success("삭제되었습니다. 응시자가 재시험을 볼 수 있습니다.")
                            st.session_state.pop(f"confirm_del_{exam_id}", None)
                            st.cache_data.clear()
                            st.rerun()
                with c2:
                    if st.button("❌ 취소", key=f"confirm_no_{exam_id}"):
                        st.session_state.pop(f"confirm_del_{exam_id}", None)
                        st.rerun()

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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("응시자", u.get("name", "-"))
    col2.metric("객관식 자동 (총합)", f"{exam.get('mc_score', 0) * 5}점 / 360점")
    col3.metric("현재 상태", {"submitted": "채점 대기", "graded": "채점 완료"}.get(exam["status"], exam["status"]))
    col4.metric("필기 결과", exam.get("written_result") or "미채점")

    # Per-area MC score breakdown
    area_mc = get_area_mc_scores(exam["id"])
    st.markdown("**분야별 객관식 점수**")
    mc_cols = st.columns(4)
    for i, area in enumerate(areas):
        aid = area["area_id"]
        correct = area_mc.get(aid, 0)
        pts = correct * 5
        mc_cols[i].metric(f"분야{aid} MC", f"{pts}점 / 90점", f"{correct}/18 정답")

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

    # Load existing per-area SA scores
    import json as _json
    _existing_sa = {}
    try:
        _existing_sa = {int(k): v for k, v in _json.loads(exam.get("sa_scores") or "{}").items()}
    except Exception:
        pass

    with st.form(f"score_form_{exam['id']}"):
        st.markdown("**주관식 점수 (분야별, 각 0~10점)**")
        st.caption("각 분야 주관식 2문제 × 5점 = 최대 10점")
        sa_cols = st.columns(4)
        sa_vals = {}
        for i, area in enumerate(areas):
            aid = area["area_id"]
            with sa_cols[i]:
                sa_vals[aid] = st.number_input(
                    f"분야{aid} 주관식",
                    min_value=0, max_value=10,
                    value=_existing_sa.get(aid, 0),
                    step=1,
                    key=f"sa_{aid}_{exam['id']}",
                )

        st.divider()
        st.markdown("**실기시험 (필기 합격자만)**")
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
        save = st.form_submit_button("💾 저장 및 합격 판정", type="primary", use_container_width=True)

    if save:
        ok = update_practical_score(
            exam["id"],
            int(practical_score),
            practical_result,
            practical_notes,
            {k: int(v) for k, v in sa_vals.items()},
        )
        if ok:
            # Preview calculated result
            _area_mc = get_area_mc_scores(exam["id"])
            _written, _area_totals = calculate_written_result(_area_mc, {k: int(v) for k, v in sa_vals.items()})
            st.success(f"저장 완료! 필기 판정: **{_written}**")
            st.caption(f"분야별 점수: {', '.join(f'분야{k}: {v}점' for k, v in sorted(_area_totals.items()))}")
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

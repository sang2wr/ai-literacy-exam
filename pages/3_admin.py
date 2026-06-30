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
    else:
        # ── 응시자 선택 ───────────────────────────────────────────────────────
        options = {}
        for e in exams_all:
            u = e.get("users") or {}
            label = f"{u.get('name','?')} ({u.get('email','?')})  —  {e.get('submitted_at','')[:16]}  [{e['status']}]"
            options[label] = e

        selected_label = st.selectbox("채점할 응시자 선택", list(options.keys()))
        exam = options[selected_label]
        exam_id = exam["id"]
        u = exam.get("users") or {}

        # ── 기존 주관식 점수 로드 (문항별) ───────────────────────────────────
        existing_q_scores = {}
        try:
            raw = json.loads(exam.get("sa_scores") or "{}")
            for k, v in raw.items():
                k_int = int(k)
                # 문항 ID는 항상 > 4 (분야 ID는 1~4)
                if k_int > 4:
                    existing_q_scores[k_int] = int(v)
        except Exception:
            pass

        # 전체 주관식 문항 목록
        sa_qs_all = [q for area in areas for q in area["questions"] if q["type"] == "sa"]

        # session_state 초기화 (문항별, 시험별 고유 key)
        for q in sa_qs_all:
            sk = f"sa_q_{exam_id}_{q['id']}"
            if sk not in st.session_state:
                st.session_state[sk] = existing_q_scores.get(q["id"], 0)

        # ── 객관식 점수 계산 ──────────────────────────────────────────────────
        area_mc = get_area_mc_scores(exam_id)
        mc_pts_total = sum(v * 5 for v in area_mc.values())

        # 현재 주관식 총점 (실시간)
        sa_pts_total = sum(
            st.session_state.get(f"sa_q_{exam_id}_{q['id']}", 0)
            for q in sa_qs_all
        )
        written_subtotal = mc_pts_total + sa_pts_total

        # ── 실시간 점수 헤더 ──────────────────────────────────────────────────
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("응시자", u.get("name", "-"))
        h2.metric("객관식 합계", f"{mc_pts_total}점 / 360점")
        h3.metric("주관식 합계", f"{sa_pts_total}점 / 40점")
        h4.metric(
            "필기 소계",
            f"{written_subtotal}점 / 400점",
            delta=f"평균 {written_subtotal/4:.1f}점",
        )

        # 분야별 MC 점수
        st.markdown("**분야별 객관식 점수**")
        mc_cols = st.columns(4)
        for i, area in enumerate(areas):
            aid = area["area_id"]
            correct = area_mc.get(aid, 0)
            pts = correct * 5
            mc_cols[i].metric(f"분야{aid} MC", f"{pts}점/90점", f"{correct}/18")

        st.divider()

        # ── 주관식 채점 (답안 + 점수 입력 인라인) ────────────────────────────
        st.markdown("### 📝 주관식 채점")
        answers = get_exam_answers(exam_id)
        ans_map = {a["question_id"]: a for a in answers}

        for area in areas:
            sa_qs = [q for q in area["questions"] if q["type"] == "sa"]
            if not sa_qs:
                continue

            # 분야별 SA 소계
            area_sa_pts = sum(
                st.session_state.get(f"sa_q_{exam_id}_{q['id']}", 0)
                for q in sa_qs
            )
            area_mc_pts = area_mc.get(area["area_id"], 0) * 5
            area_total = area_mc_pts + area_sa_pts
            badge = "✅" if area_total >= 50 else "❌"

            with st.expander(
                f"**분야 {area['area_id']}: {area['area_name']}**  "
                f"{badge} {area_total}/100점  (MC {area_mc_pts} + SA {area_sa_pts})",
                expanded=True,
            ):
                for q in sa_qs:
                    qid = q["id"]
                    sk = f"sa_q_{exam_id}_{qid}"
                    ans_row = ans_map.get(qid)
                    user_ans = (ans_row["answer_text"] if ans_row else "") or ""

                    col_q, col_score = st.columns([5, 1])
                    with col_q:
                        st.markdown(f"**{qid}번.** {q['text']}")
                        if q.get("answer"):
                            st.caption(f"📌 예시 답안: {q['answer'][:80]}{'...' if len(q.get('answer','')) > 80 else ''}")
                        st.text_area(
                            "응시자 답안",
                            value=user_ans or "미응답",
                            height=90,
                            disabled=True,
                            key=f"view_{exam_id}_{qid}",
                        )
                    with col_score:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.number_input(
                            "점수",
                            min_value=0, max_value=5,
                            step=1,
                            key=sk,
                            help="0~5점 (5점 만점)",
                        )

        # ── 저장 폼 (실기 점수 + 최종 제출) ──────────────────────────────────
        st.divider()
        st.markdown("### 💾 저장 및 실기 점수 입력")

        with st.form(f"save_form_{exam_id}"):
            st.markdown("**실기시험 (필기 합격자만)**")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                practical_score = st.number_input(
                    "실기 점수",
                    min_value=0, max_value=100,
                    value=exam.get("practical_score") or 0,
                    step=1,
                )
            with col_p2:
                practical_result = st.selectbox(
                    "실기 결과",
                    ["", "합격", "불합격"],
                    index=["", "합격", "불합격"].index(exam.get("practical_result") or ""),
                )
            practical_notes = st.text_area(
                "강사 코멘트 (선택)",
                value=exam.get("practical_notes") or "",
                height=70,
            )
            save = st.form_submit_button(
                "💾 점수 저장 및 합격 판정",
                type="primary",
                use_container_width=True,
            )

        if save:
            try:
                # 문항별 SA 점수 수집
                sa_per_q = {
                    q["id"]: int(st.session_state.get(f"sa_q_{exam_id}_{q['id']}", 0) or 0)
                    for q in sa_qs_all
                }
                # 분야별 SA 집계
                sa_per_area = {}
                for _area in areas:
                    _aid = _area["area_id"]
                    sa_per_area[_aid] = sum(
                        sa_per_q.get(q["id"], 0)
                        for q in _area["questions"] if q["type"] == "sa"
                    )

                ok = update_practical_score(
                    exam_id,
                    int(practical_score or 0),
                    practical_result,
                    practical_notes,
                    sa_per_area,
                    sa_per_q,
                )
            except Exception as _save_err:
                st.error(f"저장 오류 [{type(_save_err).__name__}]: {str(_save_err)[:300]}")
                ok = False

            if ok:
                _written, _area_totals = calculate_written_result(area_mc, sa_per_area)
                st.success(f"저장 완료!  필기 판정: **{_written}**")
                st.caption(
                    "  |  ".join(
                        f"분야{k}: {v}점" for k, v in sorted(_area_totals.items())
                    )
                )
                st.cache_data.clear()
            elif ok is False:
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

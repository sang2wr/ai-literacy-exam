from supabase import create_client, Client
import streamlit as st
import json
from typing import Optional, Dict, List
from datetime import datetime, timezone


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    # service_role key bypasses RLS — falls back to anon_key if not set
    key = st.secrets["supabase"].get("service_role_key") or st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


# ── User ──────────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[Dict]:
    try:
        res = get_client().table("users").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def create_user(email: str, password_hash: str, name: str, phone: str) -> Dict:
    res = get_client().table("users").insert({
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "phone": phone,
        "is_admin": False,
    }).execute()
    return res.data[0]


# ── Exam ──────────────────────────────────────────────────────────────────────

def get_active_exam(user_id: str) -> Optional[Dict]:
    """Return an in-progress exam for the user, if any."""
    try:
        res = (
            get_client()
            .table("exams")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "in_progress")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception:
        return None


def create_exam(user_id: str) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    res = get_client().table("exams").insert({
        "user_id": user_id,
        "started_at": now,
        "status": "in_progress",
        "mc_score": 0,
    }).execute()
    return res.data[0]


def submit_exam(exam_id: str, answers: List[Dict], mc_score: int) -> bool:
    """Save all answers and mark exam as submitted."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        # Save answers
        if answers:
            get_client().table("answers").insert(answers).execute()
        # Update exam
        get_client().table("exams").update({
            "submitted_at": now,
            "status": "submitted",
            "mc_score": mc_score,
        }).eq("id", exam_id).execute()
        return True
    except Exception as e:
        st.error(f"제출 오류: {e}")
        return False


def get_user_exams(user_id: str) -> List[Dict]:
    try:
        res = (
            get_client()
            .table("exams")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


# ── Admin ─────────────────────────────────────────────────────────────────────

def get_all_exams_with_users() -> List[Dict]:
    try:
        res = (
            get_client()
            .table("exams")
            .select("*, users(name, email, phone)")
            .neq("status", "in_progress")
            .order("submitted_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def get_exam_answers(exam_id: str) -> List[Dict]:
    try:
        res = (
            get_client()
            .table("answers")
            .select("*")
            .eq("exam_id", exam_id)
            .order("question_id")
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def get_area_mc_scores(exam_id: str) -> Dict[int, int]:
    """Returns {area_id: correct_mc_count} for each area."""
    try:
        res = (
            get_client()
            .table("answers")
            .select("area_id, is_correct")
            .eq("exam_id", exam_id)
            .execute()
        )
        scores: Dict[int, int] = {}
        for row in (res.data or []):
            if row.get("is_correct"):
                aid = int(row["area_id"])
                scores[aid] = scores.get(aid, 0) + 1
        return scores
    except Exception:
        return {}


def calculate_written_result(
    area_mc_correct: Dict[int, int],
    area_sa_pts: Dict[int, int],
) -> tuple:
    """
    area_mc_correct: {area_id: number_of_correct_mc_answers}  (0-18 each)
    area_sa_pts:     {area_id: sa_points}                     (0-10 each)
    Returns (result: str, area_totals: dict)
      result: '합격' or '탈락'
      area_totals: {area_id: total_score}  (0-100 each)
    """
    area_totals: Dict[int, int] = {}
    for aid in [1, 2, 3, 4]:
        mc_pts = area_mc_correct.get(aid, 0) * 5   # 18 MC × 5pt max = 90
        sa_pts = area_sa_pts.get(aid, 0)            # 2 SA × 5pt max = 10
        area_totals[aid] = mc_pts + sa_pts

    # 분야별 50점 미만 탈락
    if any(s < 50 for s in area_totals.values()):
        return "탈락", area_totals

    avg = sum(area_totals.values()) / 4
    return ("합격" if avg >= 60 else "탈락"), area_totals


def get_exam_by_id(exam_id: str) -> Optional[Dict]:
    try:
        res = get_client().table("exams").select("*").eq("id", exam_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def delete_exam(exam_id: str) -> bool:
    try:
        get_client().table("answers").delete().eq("exam_id", exam_id).execute()
        get_client().table("exams").delete().eq("id", exam_id).execute()
        return True
    except Exception as e:
        st.error(f"삭제 오류: {e}")
        return False


def update_practical_score(
    exam_id: str,
    practical_score: Optional[int],
    practical_result: str,
    practical_notes: str,
    sa_scores_dict: Dict[int, int],   # {1: pts, 2: pts, 3: pts, 4: pts}
) -> bool:
    """Save scores, calculate per-area totals, and determine written_result."""
    try:
        sa_score_total = sum(sa_scores_dict.values())
        area_mc = get_area_mc_scores(exam_id)
        written_result, _ = calculate_written_result(area_mc, sa_scores_dict)

        get_client().table("exams").update({
            "practical_score": practical_score,
            "practical_result": practical_result,
            "practical_notes": practical_notes,
            "sa_score": sa_score_total,
            "sa_scores": json.dumps({str(k): v for k, v in sa_scores_dict.items()}),
            "written_result": written_result,
            "total_score": practical_score or 0,
            "status": "graded",
        }).eq("id", exam_id).execute()
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

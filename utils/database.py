from supabase import create_client, Client
import streamlit as st
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


def update_practical_score(
    exam_id: str,
    practical_score: Optional[int],
    practical_result: str,
    practical_notes: str,
    sa_score: int,
) -> bool:
    try:
        total = (0 if practical_score is None else practical_score)
        get_client().table("exams").update({
            "practical_score": practical_score,
            "practical_result": practical_result,
            "practical_notes": practical_notes,
            "sa_score": sa_score,
            "total_score": total,
            "status": "graded",
        }).eq("id", exam_id).execute()
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

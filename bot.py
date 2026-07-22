"""
AI리터러시지도사 자격시험 관리 텔레그램 봇
실행: python bot.py  (ai_exam 폴더에서)
"""
import os
import json
import logging
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
)

from utils.database import (
    get_all_exams_with_users, get_exam_answers, get_exam_by_id,
    update_practical_score, delete_exam,
    get_area_mc_scores, calculate_written_result,
)
from utils.questions import load_questions

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_IDS   = [int(x) for x in os.environ.get("TELEGRAM_ADMIN_IDS", "").split(",") if x.strip()]

# 응시자 번호 ↔ exam_id 캐시 (세션 유지용)
_exam_cache: dict[int, str] = {}


# ── 유틸 ──────────────────────────────────────────────────────────────────────

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def fmt_dt(s: str) -> str:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%m/%d %H:%M")
    except Exception:
        return s[:16] if s else "-"

def get_cached_exam(idx: int) -> str | None:
    return _exam_cache.get(idx)

def truncate(text: str, limit: int = 3800) -> str:
    return text if len(text) <= limit else text[:limit] + "\n…(생략)"


# ── 권한 데코레이터 ────────────────────────────────────────────────────────────

def admin_only(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ 관리자만 사용 가능합니다.")
            return
        await func(update, ctx)
    return wrapper


# ── /start, /help ─────────────────────────────────────────────────────────────

@admin_only
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *AI리터러시지도사 시험 관리 봇*\n\n"
        "/list — 제출된 시험 목록\n"
        "/detail `[번호]` — 주관식 답안 보기\n"
        "/score `[번호] [점수×8]` — 주관식 채점\n"
        "/practical `[번호] [합격/불합격] [점수]` — 실기 결과\n"
        "/delete `[번호]` — 기록 삭제 \\(재시험\\)\n\n"
        "채점 점수 순서: 분야1\\-Q1, 분야1\\-Q2, 분야2\\-Q1 \\.\\.\\. 분야4\\-Q2",
        parse_mode="MarkdownV2",
    )


# ── /list ─────────────────────────────────────────────────────────────────────

@admin_only
async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    exams = get_all_exams_with_users()
    if not exams:
        await update.message.reply_text("제출된 시험이 없습니다.")
        return

    _exam_cache.clear()
    lines = ["📋 *제출된 시험 목록*\n"]
    for i, e in enumerate(exams, 1):
        _exam_cache[i] = e["id"]
        u = e.get("users") or {}
        mc  = (e.get("mc_score") or 0) * 5
        wr  = e.get("written_result") or "미채점"
        pr  = e.get("practical_result") or "-"
        st  = {"submitted": "채점대기", "graded": "채점완료"}.get(e["status"], e["status"])
        lines.append(
            f"{i}\\. *{u.get('name','-')}* \\| {fmt_dt(e.get('submitted_at',''))}\n"
            f"   {st} \\| MC {mc}pt \\| 필기:{wr} \\| 실기:{pr}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


# ── /detail [번호] ────────────────────────────────────────────────────────────

@admin_only
async def cmd_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("사용법: /detail [번호]\n먼저 /list 를 실행하세요.")
        return

    try:
        idx = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("번호를 숫자로 입력하세요.")
        return

    exam_id = get_cached_exam(idx)
    if not exam_id:
        await update.message.reply_text("먼저 /list 를 실행하세요.")
        return

    exams = get_all_exams_with_users()
    exam = next((e for e in exams if e["id"] == exam_id), None)
    if not exam:
        await update.message.reply_text("시험을 찾을 수 없습니다.")
        return

    u       = exam.get("users") or {}
    areas   = load_questions(exam.get("question_version"))
    answers = get_exam_answers(exam_id)
    ans_map = {a["question_id"]: a["answer_text"] for a in answers}
    area_mc = get_area_mc_scores(exam_id)

    try:
        existing_scores = {int(k): v for k, v in json.loads(exam.get("sa_scores") or "{}").items() if int(k) > 4}
    except Exception:
        existing_scores = {}

    lines = [
        f"👤 *{u.get('name','-')}* \\({u.get('email','-')}\\)",
        f"제출: {fmt_dt(exam.get('submitted_at',''))}",
        "",
    ]

    sa_order = []
    for area in areas:
        aid = area["area_id"]
        mc_pts = area_mc.get(aid, 0) * 5
        lines.append(f"📚 *분야{aid}: {area['area_name']}* — MC {mc_pts}pt/90pt")
        sa_qs = [q for q in area["questions"] if q["type"] == "sa"]
        for q in sa_qs:
            sa_order.append(q["id"])
            ans = (ans_map.get(q["id"]) or "미응답")[:80]
            cur = existing_scores.get(q["id"], "\\-")
            lines.append(f"  Q{q['id']}\\. {q['text'][:40]}\\.\\.\\.")
            lines.append(f"  답: {ans}")
            lines.append(f"  현재점수: {cur}/5")
        lines.append("")

    lines.append(f"💾 채점: `/score {idx} 5 4 3 5 4 3 5 4`")
    lines.append(f"순서: {' \\> '.join(str(qid) for qid in sa_order)}")

    await update.message.reply_text(
        truncate("\n".join(lines)), parse_mode="MarkdownV2"
    )


# ── /score [번호] [점수×8] ────────────────────────────────────────────────────

@admin_only
async def cmd_score(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 9:
        await update.message.reply_text(
            "사용법: /score [번호] [점수 8개, 0-5]\n"
            "예시: /score 1 5 4 3 5 4 3 5 4\n"
            "순서: 분야1-Q1, 분야1-Q2, 분야2-Q1, 분야2-Q2, 분야3-Q1, 분야3-Q2, 분야4-Q1, 분야4-Q2"
        )
        return

    try:
        idx    = int(ctx.args[0])
        scores = [int(x) for x in ctx.args[1:9]]
    except ValueError:
        await update.message.reply_text("숫자만 입력하세요.")
        return

    if any(s < 0 or s > 5 for s in scores):
        await update.message.reply_text("각 점수는 0~5 사이여야 합니다.")
        return

    exam_id = get_cached_exam(idx)
    if not exam_id:
        await update.message.reply_text("먼저 /list 를 실행하세요.")
        return

    # 기존 실기 값 유지 + 문제 버전 확인
    exams = get_all_exams_with_users()
    exam  = next((e for e in exams if e["id"] == exam_id), {})
    areas = load_questions(exam.get("question_version"))

    # 문항별 점수 매핑
    sa_per_q: dict[int, int] = {}
    sa_per_area: dict[int, int] = {}
    score_idx = 0
    for area in areas:
        aid  = area["area_id"]
        sa_qs = [q for q in area["questions"] if q["type"] == "sa"]
        area_total = 0
        for q in sa_qs:
            if score_idx < len(scores):
                sa_per_q[q["id"]]  = scores[score_idx]
                area_total         += scores[score_idx]
                score_idx          += 1
        sa_per_area[aid] = area_total

    ok = update_practical_score(
        exam_id,
        exam.get("practical_score") or 0,
        exam.get("practical_result") or "",
        exam.get("practical_notes") or "",
        sa_per_area,
        sa_per_q,
    )

    if ok:
        area_mc = get_area_mc_scores(exam_id)
        written, area_totals = calculate_written_result(area_mc, sa_per_area)
        detail = " | ".join(f"분야{k}:{v}점" for k, v in sorted(area_totals.items()))
        await update.message.reply_text(f"✅ 채점 완료!\n필기 판정: {written}\n{detail}")
    else:
        await update.message.reply_text("❌ 저장 실패. 다시 시도해주세요.")


# ── /practical [번호] [합격/불합격] [점수] ────────────────────────────────────

@admin_only
async def cmd_practical(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "사용법: /practical [번호] [합격/불합격] [점수(선택)]\n"
            "예시: /practical 1 합격 85"
        )
        return

    try:
        idx = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("번호를 숫자로 입력하세요.")
        return

    result = ctx.args[1]
    if result not in ("합격", "불합격"):
        await update.message.reply_text("결과는 '합격' 또는 '불합격'으로 입력하세요.")
        return

    p_score = 0
    if len(ctx.args) >= 3:
        try:
            p_score = int(ctx.args[2])
        except ValueError:
            pass

    exam_id = get_cached_exam(idx)
    if not exam_id:
        await update.message.reply_text("먼저 /list 를 실행하세요.")
        return

    exams = get_all_exams_with_users()
    exam  = next((e for e in exams if e["id"] == exam_id), None)
    if not exam:
        await update.message.reply_text("시험을 찾을 수 없습니다.")
        return

    # 기존 주관식 점수 복원
    try:
        sa_per_q = {int(k): v for k, v in json.loads(exam.get("sa_scores") or "{}").items() if int(k) > 4}
    except Exception:
        sa_per_q = {}

    areas = load_questions(exam.get("question_version"))
    sa_per_area: dict[int, int] = {}
    for area in areas:
        aid   = area["area_id"]
        sa_qs = [q for q in area["questions"] if q["type"] == "sa"]
        sa_per_area[aid] = sum(sa_per_q.get(q["id"], 0) for q in sa_qs)

    ok = update_practical_score(
        exam_id, p_score, result,
        exam.get("practical_notes") or "",
        sa_per_area,
        sa_per_q or None,
    )

    if ok:
        await update.message.reply_text(f"✅ 실기 결과 저장!\n결과: {result} | 점수: {p_score}점")
    else:
        await update.message.reply_text("❌ 저장 실패.")


# ── /delete [번호] ────────────────────────────────────────────────────────────

@admin_only
async def cmd_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("사용법: /delete [번호]")
        return

    try:
        idx = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("번호를 숫자로 입력하세요.")
        return

    exam_id = get_cached_exam(idx)
    if not exam_id:
        await update.message.reply_text("먼저 /list 를 실행하세요.")
        return

    exams = get_all_exams_with_users()
    exam  = next((e for e in exams if e["id"] == exam_id), None)
    u     = (exam.get("users") or {}) if exam else {}

    keyboard = [[
        InlineKeyboardButton("✅ 삭제 확인", callback_data=f"del:{exam_id}"),
        InlineKeyboardButton("❌ 취소",      callback_data="del:cancel"),
    ]]
    await update.message.reply_text(
        f"⚠️ {u.get('name','-')}님의 시험 기록을 삭제하시겠습니까?\n삭제 후 재시험이 가능합니다.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def btn_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ 권한 없음")
        return

    data = query.data
    if data == "del:cancel":
        await query.edit_message_text("취소되었습니다.")
    elif data.startswith("del:"):
        exam_id = data[4:]
        if delete_exam(exam_id):
            await query.edit_message_text("✅ 삭제 완료. 응시자가 재시험을 볼 수 있습니다.")
        else:
            await query.edit_message_text("❌ 삭제 실패.")


# ── 새 시험 제출 알림 (60초마다) ──────────────────────────────────────────────

async def notify_new_submissions(ctx: ContextTypes.DEFAULT_TYPE):
    seen: set = ctx.bot_data.setdefault("seen_exams", set())
    exams = get_all_exams_with_users()
    for e in exams:
        if e["id"] not in seen:
            seen.add(e["id"])
            # 봇 시작 시 기존 시험은 알림 없이 등록만
            if ctx.bot_data.get("initialized"):
                u = e.get("users") or {}
                for admin_id in ADMIN_IDS:
                    try:
                        await ctx.bot.send_message(
                            admin_id,
                            f"📬 새 시험 제출!\n"
                            f"👤 {u.get('name','-')} ({u.get('email','-')})\n"
                            f"📅 {fmt_dt(e.get('submitted_at',''))}\n"
                            f"/list 로 확인하세요."
                        )
                    except Exception as err:
                        logger.warning("알림 전송 실패: %s", err)

    ctx.bot_data["initialized"] = True


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise RuntimeError(".env 파일에 TELEGRAM_BOT_TOKEN 을 설정하세요.")
    if not ADMIN_IDS:
        raise RuntimeError(".env 파일에 TELEGRAM_ADMIN_IDS 를 설정하세요.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler(["start", "help"],   cmd_start))
    app.add_handler(CommandHandler("list",              cmd_list))
    app.add_handler(CommandHandler("detail",            cmd_detail))
    app.add_handler(CommandHandler("score",             cmd_score))
    app.add_handler(CommandHandler("practical",         cmd_practical))
    app.add_handler(CommandHandler("delete",            cmd_delete))
    app.add_handler(CallbackQueryHandler(btn_callback))

    app.job_queue.run_repeating(notify_new_submissions, interval=60, first=5)

    logger.info("봇 시작! 관리자 ID: %s", ADMIN_IDS)
    app.run_polling()


if __name__ == "__main__":
    main()

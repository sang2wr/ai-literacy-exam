"""자격증 PDF 생성 — 세로 A4, 금박 테두리가 인쇄된 용지에 겹쳐 찍는 용도.

**이 파일 자체에는 테두리를 그리지 않는다.** 인쇄는 금박 테두리가 이미 있는 A4 용지에 하므로,
그 테두리를 침범하지 않도록 안전 여백을 둔다 (2026-08-20, 실사용자 지정):
  - 상하 3cm, 좌우 2.5cm는 기본적으로 비운다.
  - 네 모서리는 테두리의 장식(코너 문양)이 더 크게 파고들기 때문에, 페이지의 실제 꼭짓점에서
    대각선 거리로 5.5cm 안쪽까지는 아무것도 놓지 않는다. 즉 y가 상단/하단 끝에서 대략 5cm
    안쪽으로 들어오기 전까지는 좌우 2.5cm보다 더 안쪽(더 크게 인셋)에 둬야 한다 —
    실제로는 상단·하단에 아주 짧고 가운데 정렬된 텍스트만 두는 방식으로 피해간다.

한글은 나눔고딕/나눔명조(OFL 오픈소스, 임베딩 자유)를 `assets/fonts/`에 직접 임베딩해서 쓴다.
reportlab 내장 CID 폰트(HYSMyeongJo 등)는 뷰어에 그 폰트가 없으면 텍스트는 추출되는데 화면엔
빈칸으로 보이는 문제가 있어(실제로 겪음) 쓰지 않는다.

레이아웃과 문구는 사용자가 이전에 만들어 둔 참고본
(`상상우리 AI리터러시지도사 자격증_샘플.pdf`, 가로형)을 세로형으로 옮긴 것이다.
직인(`assets/seal.png`)은 `(직인) 주식회사상상우리.png`에서 그대로 가져왔다.
"""
from pathlib import Path
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from utils.theme import BRAND, logo_path

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_DIR = ASSET_DIR / "fonts"
SEAL_PATH = ASSET_DIR / "seal.png"

SERIF = "NanumMyeongjo"
GOTHIC = "NanumGothic"
GOTHIC_BOLD = "NanumGothicBold"

ORG_NAME = "주식회사 상상우리"
ORG_CEO = "신철호"
ORG_BIZ_NO = "117-81-84651"
ORG_ADDRESS = "서울특별시 중구 수표로 12 (충무로3가) 11층"
QUAL_NAME = "AI리터러시지도사"
QUAL_NAME_EN = "AI LITERACY INSTRUCTOR"
QUAL_REG_NO = "제2025-006361호"   # 한국직업능력연구원 등록 민간자격 번호

_fonts_ready = False


def _ensure_fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    registerFont(TTFont(SERIF, str(FONT_DIR / "NanumMyeongjo.ttf")))
    registerFont(TTFont(GOTHIC, str(FONT_DIR / "NanumGothic.ttf")))
    registerFont(TTFont(GOTHIC_BOLD, str(FONT_DIR / "NanumGothicBold.ttf")))
    _fonts_ready = True


def _spaced(s: str) -> str:
    """글자 사이를 살짝 벌려 증서 제목다운 느낌을 낸다 ('자격증' → '자 격 증')."""
    return " ".join(list(s))


def _wrap(text: str, font: str, size: float, max_width: float) -> list:
    """max_width(포인트) 안에 들어오도록 어절 단위로 줄바꿈."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if stringWidth(trial, font, size) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class _NullCanvas:
    """실제로 그리지 않고 y_cur 흐름만 재현하기 위한 가짜 캔버스 —
    상하 여백을 맞추려면 그리기 전에 콘텐츠가 어디서 끝나는지 먼저 알아야 한다."""
    def __getattr__(self, _name):
        return lambda *a, **kw: None


def _content_top_start(H) -> float:
    return H - 46 * mm   # 상단: 3cm 여백 + 모서리 대각선 여유를 더한 시작점


def _measure_bottom_margin(W, H, name: str, cert_no: str, issued_date: str) -> float:
    """콘텐츠를 실제로 그리지 않고 마지막 줄이 페이지 하단에서 얼마나 떨어지는지만 계산한다."""
    return _draw_certificate_page(_NullCanvas(), W, H, name, cert_no, issued_date)


def _draw_certificate_page(c, W, H, name: str, cert_no: str, issued_date: str, y_shift: float = 0) -> float:
    """캔버스 한 페이지에 자격증 한 장을 그린다. showPage/save는 호출부 책임 —
    일괄 출력(batch)에서는 여러 사람을 한 Canvas에 이어 그려야 하기 때문이다.
    반환값은 마지막 줄이 끝난 y좌표(= 실제 하단 여백) — 상하 여백을 맞출 때 씀."""
    ink = HexColor(BRAND["ink"])
    teal = HexColor(BRAND["teal"])
    muted = HexColor(BRAND["muted"])

    try:
        y, m, d = issued_date.split("-")
        issued_label = f"{y}년 {int(m)}월 {int(d)}일"
    except Exception:
        issued_label = issued_date

    cx = W / 2
    left, right = 42 * mm, W - 42 * mm   # 본문 좌우 기준선 (2.5cm 여백보다 더 안쪽 — 모서리 여유용)
    y_cur = _content_top_start(H) + y_shift

    # ── 상단: 자격증 번호 · 등록번호 (가운데 정렬 한 줄 — 모서리를 피하려고 좌우로 안 쪼갠다) ──
    c.setFont(SERIF, 9.5)
    c.setFillColor(muted)
    c.drawCentredString(cx, y_cur, f"제 {cert_no} 호   ·   등록민간자격 {QUAL_REG_NO}")
    y_cur -= 16 * mm

    # ── 로고 아이콘 ──
    try:
        logo_w = 20 * mm
        logo_h = logo_w
        c.drawImage(
            logo_path("icon"), cx - logo_w / 2, y_cur - logo_h,
            width=logo_w, height=logo_h, preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        pass
    y_cur -= logo_h + 12 * mm

    # ── 제목 ──
    c.setFillColor(ink)
    c.setFont(GOTHIC_BOLD, 30)
    c.drawCentredString(cx, y_cur, _spaced("자격증"))
    y_cur -= 12 * mm

    c.setFont(SERIF, 9)
    c.setFillColor(muted)
    c.drawCentredString(cx, y_cur, f"자 격 종 목 · QUALIFICATION")
    y_cur -= 9 * mm

    c.setFillColor(ink)
    c.setFont(GOTHIC_BOLD, 20)
    c.drawCentredString(cx, y_cur, _spaced(QUAL_NAME))
    y_cur -= 14 * mm

    # 단일등급 배지 (badge_cy: 타원 세로 중심)
    badge_w, badge_h = 30 * mm, 8 * mm
    badge_cy = y_cur - 2 * mm
    c.setStrokeColor(teal)
    c.setLineWidth(0.9)
    c.roundRect(cx - badge_w / 2, badge_cy - badge_h / 2, badge_w, badge_h, 4 * mm, stroke=1, fill=0)
    c.setFont(GOTHIC, 10)
    c.setFillColor(teal)
    # 한글 글자는 베이스라인 위로 그려지므로, 상자 정중앙에 시각적으로 오려면
    # 베이스라인을 중심보다 살짝(글자 크기의 ~0.36배) 아래에 둬야 한다.
    c.drawCentredString(cx, badge_cy - 0.36 * 10, "단일등급")
    y_cur = badge_cy - badge_h / 2 - 10 * mm

    # ── 표: 성명 / 자격번호 / 취득일자 ──
    row_h = 12.5 * mm
    table_top = y_cur
    rows = [("성  명", name), ("자 격 번 호", cert_no), ("취 득 일 자", issued_label)]
    c.setLineWidth(0.6)
    c.setStrokeColor(HexColor(BRAND["border"]))
    c.line(left, table_top, right, table_top)
    ry = table_top
    for label, value in rows:
        ry -= row_h
        c.line(left, ry, right, ry)
        c.setFont(SERIF, 11)
        c.setFillColor(muted)
        c.drawString(left + 3 * mm, ry + row_h / 2 - 3.2 * mm, label)
        c.setFont(GOTHIC_BOLD, 13)
        c.setFillColor(ink)
        c.drawRightString(right - 3 * mm, ry + row_h / 2 - 3.6 * mm, str(value))
    y_cur = ry - 12 * mm

    # ── 본문 ──
    body_lines = [
        f"위 사람은 「자격기본법」 제17조제2항에 따라 등록된 민간자격",
        f"{QUAL_NAME} 검정에서 {ORG_NAME} 자격관리·운영 규정이 정한",
        "기준을 통과하였으므로 이 증서를 수여합니다.",
    ]
    c.setFont(SERIF, 11.5)
    c.setFillColor(ink)
    for line in body_lines:
        c.drawCentredString(cx, y_cur, line)
        y_cur -= 6.8 * mm
    y_cur -= 6 * mm

    # ── 발급일 ──
    c.setFont(SERIF, 11)
    c.drawCentredString(cx, y_cur, issued_label)
    y_cur -= 15 * mm   # 아래 직인이 실물 크기(3cm)라 커서, 위 줄과 안 겹치게 여유를 더 둔다

    # ── 발급기관 · 대표이사 (직인은 이 두 줄에 걸치도록 오른쪽에 겹쳐 찍는다) ──
    org_font_size = 15
    org_y = y_cur
    c.setFont(GOTHIC_BOLD, org_font_size)
    c.drawCentredString(cx, org_y, ORG_NAME)
    org_half_w = stringWidth(ORG_NAME, GOTHIC_BOLD, org_font_size) / 2
    ceo_y = org_y - 9 * mm
    c.setFont(SERIF, 11)
    c.drawCentredString(cx, ceo_y, f"대표이사   {ORG_CEO}")

    seal_bottom = ceo_y
    try:
        seal_size = 30 * mm   # 실제 인쇄 크기(가로세로 3cm)에 맞춤
        seal_cx = cx + org_half_w + 3 * mm + seal_size / 2   # 기관명 글자 폭을 실측해서 겹치지 않게
        seal_cx = min(seal_cx, right - seal_size / 2)        # 오른쪽 안전 여백선을 넘지 않도록
        seal_cy = org_y - 2 * mm
        seal_angle = 2  # 원본 이미지 자체가 살짝 시계방향으로 기울어 보여 반시계로 보정 (양수 = 반시계 방향)
        c.saveState()
        c.translate(seal_cx, seal_cy)
        c.rotate(seal_angle)
        c.drawImage(
            str(SEAL_PATH), -seal_size / 2, -seal_size / 2,
            width=seal_size, height=seal_size, preserveAspectRatio=True, mask="auto",
        )
        c.restoreState()
        seal_bottom = seal_cy - seal_size / 2
    except Exception:
        pass
    y_cur = min(ceo_y, seal_bottom) - 10 * mm

    # ── 하단 법정 고지 (짧게 줄여 모서리 여유를 확보) ──
    # 주소를 발급기관 줄에 붙이면 어절 단위 줄바꿈에서 "11층"만 혼자 다음 줄로
    # 떨어지는 경우가 있어(실제로 겪음) — 아예 별도 줄로 뺀다.
    footer_lines = [
        f"본 자격은 「자격기본법」에 따라 한국직업능력연구원에 등록된 민간자격입니다. (등록번호 {QUAL_REG_NO})",
        f"자격관리·발급기관 {ORG_NAME} (사업자등록번호 {ORG_BIZ_NO})",
        ORG_ADDRESS,
        "자격 등록 여부는 민간자격정보서비스(www.pqi.or.kr)에서 확인하실 수 있습니다.",
    ]
    c.setFont(SERIF, 7.3)
    c.setFillColor(muted)
    max_w = right - left
    for para in footer_lines:
        for line in _wrap(para, SERIF, 7.3, max_w):
            c.drawCentredString(cx, y_cur, line)
            y_cur -= 3.4 * mm

    return y_cur


def _balancing_shift(W, H, name: str, cert_no: str, issued_date: str) -> float:
    """상단 여백과 하단 여백이 같아지도록 콘텐츠 전체를 위로 밀어올릴 양을 계산한다.
    (아래로 밀 필요가 생기는 경우, 즉 콘텐츠가 원래도 짧아서 하단이 더 넉넉한 경우는
    상단의 모서리 안전 여백을 침범하게 되므로 밀지 않는다 — 0 이하는 버림.)"""
    top_margin = H - _content_top_start(H)
    bottom_margin = _measure_bottom_margin(W, H, name, cert_no, issued_date)
    return max(0.0, (top_margin - bottom_margin) / 2)


def generate_certificate_pdf(name: str, cert_no: str, issued_date: str) -> bytes:
    """name: 수여자 성명 / cert_no: 예 '2026-001' / issued_date: 'YYYY-MM-DD'"""
    _ensure_fonts()
    buf = BytesIO()
    W, H = A4  # 세로: 210 x 297mm
    c = canvas.Canvas(buf, pagesize=(W, H))
    shift = _balancing_shift(W, H, name, cert_no, issued_date)
    _draw_certificate_page(c, W, H, name, cert_no, issued_date, y_shift=shift)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def generate_certificates_batch_pdf(entries) -> bytes:
    """합격자 여러 명의 자격증을 한 PDF에 이어 붙인다 — 한 번에 인쇄하기 위한 용도.
    entries: [(name, cert_no, issued_date), ...]. 발급번호 순으로 미리 정렬해서 넘길 것."""
    _ensure_fonts()
    buf = BytesIO()
    W, H = A4
    c = canvas.Canvas(buf, pagesize=(W, H))
    for name, cert_no, issued_date in entries:
        shift = _balancing_shift(W, H, name, cert_no, issued_date)
        _draw_certificate_page(c, W, H, name, cert_no, issued_date, y_shift=shift)
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

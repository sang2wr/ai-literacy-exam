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


def generate_certificate_pdf(name: str, cert_no: str, issued_date: str) -> bytes:
    """name: 수여자 성명 / cert_no: 예 '2026-001' / issued_date: 'YYYY-MM-DD'"""
    _ensure_fonts()

    buf = BytesIO()
    W, H = A4  # 세로: 210 x 297mm
    c = canvas.Canvas(buf, pagesize=(W, H))

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
    y_cur = H - 46 * mm                  # 상단부터: 3cm 여백 + 모서리 대각선 여유를 더한 시작점

    # ── 상단: 자격증 번호 · 등록번호 (가운데 정렬 한 줄 — 모서리를 피하려고 좌우로 안 쪼갠다) ──
    c.setFont(SERIF, 9.5)
    c.setFillColor(muted)
    c.drawCentredString(cx, y_cur, f"제 {cert_no} 호   ·   등록민간자격 {QUAL_REG_NO}")
    y_cur -= 22 * mm

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

    # 단일등급 배지
    badge_w, badge_h = 30 * mm, 8 * mm
    c.setStrokeColor(teal)
    c.setLineWidth(0.9)
    c.roundRect(cx - badge_w / 2, y_cur - badge_h + 2 * mm, badge_w, badge_h, 4 * mm, stroke=1, fill=0)
    c.setFont(GOTHIC, 10)
    c.setFillColor(teal)
    c.drawCentredString(cx, y_cur - badge_h / 2 + 2.6 * mm, "단일등급")
    y_cur -= badge_h + 10 * mm

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
    y_cur -= 8 * mm

    # ── 발급일 ──
    c.setFont(SERIF, 11)
    c.drawCentredString(cx, y_cur, issued_label)
    y_cur -= 13 * mm

    # ── 발급기관 · 대표이사 (직인은 이 두 줄에 걸치도록 오른쪽에 겹쳐 찍는다) ──
    c.setFont(GOTHIC_BOLD, 15)
    c.drawCentredString(cx, y_cur, ORG_NAME)
    y_cur -= 8 * mm
    c.setFont(SERIF, 11)
    c.drawCentredString(cx, y_cur, f"대표이사   {ORG_CEO}")

    try:
        seal_size = 20 * mm
        c.drawImage(
            str(SEAL_PATH), cx + 24 * mm, y_cur - 6 * mm,
            width=seal_size, height=seal_size, preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        pass
    y_cur -= 16 * mm

    # ── 하단 법정 고지 (짧게 줄여 모서리 여유를 확보) ──
    footer_lines = [
        f"본 자격은 「자격기본법」에 따라 한국직업능력연구원에 등록된 민간자격입니다. (등록번호 {QUAL_REG_NO})",
        f"자격관리·발급기관 {ORG_NAME} (사업자등록번호 {ORG_BIZ_NO}) · {ORG_ADDRESS}",
        "자격 등록 여부는 민간자격정보서비스(www.pqi.or.kr)에서 확인하실 수 있습니다.",
    ]
    c.setFont(SERIF, 7.3)
    c.setFillColor(muted)
    max_w = right - left
    for para in footer_lines:
        for line in _wrap(para, SERIF, 7.3, max_w):
            c.drawCentredString(cx, y_cur, line)
            y_cur -= 3.6 * mm

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

"""자격증 PDF 생성.

한글은 나눔고딕/나눔명조(OFL 오픈소스, 임베딩 자유)를 `assets/fonts/`에 넣고 직접 임베딩한다.
reportlab 내장 CID 폰트(HYSMyeongJo 등)는 뷰어가 한글 폰트를 안 갖고 있으면 빈칸으로 보이는
문제가 있어(글자는 추출되지만 화면엔 안 그려짐) 쓰지 않는다 — 임베딩해야 어떤 환경에서도 보인다.
"""
from pathlib import Path
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from utils.theme import BRAND, logo_path

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

SERIF = "NanumMyeongjo"
GOTHIC = "NanumGothic"
GOTHIC_BOLD = "NanumGothicBold"

ORG_NAME = "주식회사 상상우리"
QUAL_NAME = "AI리터러시지도사"
QUAL_NAME_EN = "AI LITERACY INSTRUCTOR"

_fonts_ready = False


def _ensure_fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    registerFont(TTFont(SERIF, str(FONT_DIR / "NanumMyeongjo.ttf")))
    registerFont(TTFont(GOTHIC, str(FONT_DIR / "NanumGothic.ttf")))
    registerFont(TTFont(GOTHIC_BOLD, str(FONT_DIR / "NanumGothicBold.ttf")))
    _fonts_ready = True


def generate_certificate_pdf(name: str, cert_no: str, issued_date: str) -> bytes:
    """name: 수여자 성명 / cert_no: 예 'AILT-2026-0001' / issued_date: 'YYYY-MM-DD'"""
    _ensure_fonts()

    buf = BytesIO()
    W, H = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(W, H))

    ink = HexColor(BRAND["ink"])
    teal = HexColor(BRAND["teal"])
    coral = HexColor(BRAND["coral"])
    muted = HexColor(BRAND["muted"])

    # 배경
    c.setFillColor(HexColor(BRAND["bg"]))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # 이중 테두리
    margin = 14 * mm
    c.setStrokeColor(teal)
    c.setLineWidth(2.4)
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin)
    c.setStrokeColor(coral)
    c.setLineWidth(0.8)
    c.rect(margin + 4 * mm, margin + 4 * mm, W - 2 * margin - 8 * mm, H - 2 * margin - 8 * mm)

    # 로고
    try:
        logo_w = 62 * mm
        logo_h = logo_w * 0.25
        c.drawImage(
            logo_path("horizontal"),
            W / 2 - logo_w / 2, H - 42 * mm,
            width=logo_w, height=logo_h,
            preserveAspectRatio=True, mask="auto",
        )
    except Exception:
        pass

    # 제목
    c.setFillColor(ink)
    c.setFont(GOTHIC_BOLD, 28)
    c.drawCentredString(W / 2, H - 62 * mm, f"{QUAL_NAME} 자격증")

    c.setFont(SERIF, 10)
    c.setFillColor(muted)
    c.drawCentredString(W / 2, H - 69 * mm, f"{QUAL_NAME_EN} CERTIFICATE")

    c.setFont(SERIF, 11)
    c.setFillColor(ink)
    c.drawCentredString(W / 2, H - 82 * mm, f"제 {cert_no} 호")

    # 성명
    c.setFont(GOTHIC_BOLD, 22)
    c.drawCentredString(W / 2, H - 104 * mm, name)
    c.setFont(SERIF, 12)
    c.drawCentredString(W / 2, H - 112 * mm, "귀하")

    # 본문
    body_lines = [
        f"위 사람은 {ORG_NAME}이(가) 시행한 「{QUAL_NAME}」 민간자격 시험에서",
        "소정의 필기 및 실기 심사를 모두 통과하였으므로 이 증서를 수여합니다.",
    ]
    c.setFont(SERIF, 12.5)
    for i, line in enumerate(body_lines):
        c.drawCentredString(W / 2, H - 128 * mm - i * 7 * mm, line)

    # 발급일 / 발급기관
    c.setFont(SERIF, 12)
    c.setFillColor(ink)
    c.drawCentredString(W / 2, margin + 28 * mm, issued_date)
    c.setFont(GOTHIC_BOLD, 15)
    c.drawCentredString(W / 2, margin + 18 * mm, f"{ORG_NAME}  대표이사")

    # 각주
    c.setFont(SERIF, 8)
    c.setFillColor(muted)
    c.drawString(
        margin + 8 * mm, margin + 6 * mm,
        f"발급번호 {cert_no}  ·  본 자격증은 「자격기본법」에 따른 등록 민간자격이며 국가 공인 자격이 아닙니다.",
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

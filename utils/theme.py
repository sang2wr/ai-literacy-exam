"""공통 디자인 시스템 — 상상우리 브랜드 컬러 / 로고 / 아이콘 / 공통 CSS·컴포넌트"""
import base64
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BRAND = {
    "ink": "#221E1F",
    "ink_soft": "#5B5658",
    "teal": "#39BCA5",
    "coral": "#F15835",
    "orange": "#F78E1D",
    "bg": "#FAFAF9",
    "card": "#FFFFFF",
    "border": "#ECE7E4",
    "muted": "#8A8583",
}

_LOGO_FILES = {
    "horizontal": "logo_horizontal.png",
    "icon": "logo_icon.png",
    "white": "logo_white.png",
}


def render_html(content: str):
    """멀티라인 HTML 문자열을 렌더링.

    st.markdown은 내부적으로 마크다운 파서를 먼저 거치는데, 줄 앞에 공백 4칸 이상이
    남아있으면 "들여쓰기된 코드블록"으로 오인해 HTML을 화면에 그대로 텍스트로 찍어버린다.
    그래서 각 줄의 앞뒤 공백을 지운 뒤 렌더링한다.
    """
    flat = "\n".join(line.strip() for line in content.strip("\n").splitlines())
    st.markdown(flat, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _b64(filename: str) -> str:
    return base64.b64encode((ASSETS / filename).read_bytes()).decode()


def logo_data_uri(variant: str = "horizontal") -> str:
    return f"data:image/png;base64,{_b64(_LOGO_FILES[variant])}"


def logo_path(variant: str = "icon") -> str:
    return str(ASSETS / _LOGO_FILES[variant])


# ── 아이콘 (Feather 스타일, stroke 기반 인라인 SVG) ─────────────────────────────
_ICON_BODY = {
    "pencil": '<path d="M4 20h4l10-10-4-4L4 16v4z"/><line x1="13" y1="7" x2="17" y2="11"/>',
    "clipboard-check": '<rect x="6" y="4" width="12" height="16" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><polyline points="9,13 11,15 15,10"/>',
    "shield": '<path d="M12 3l8 4v5c0 5-3.5 8.5-8 9-4.5-0.5-8-4-8-9V7l8-4z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><polyline points="12,7 12,12 15,14"/>',
    "book-open": '<path d="M2 5c3-2 7-2 10 0v14c-3-2-7-2-10 0V5z"/><path d="M22 5c-3-2-7-2-10 0v14c3-2 7-2 10 0V5z"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>',
    "grid": '<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><polyline points="3,7 12,13 21,7"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>',
    "user-plus": '<circle cx="9" cy="8" r="4"/><path d="M2 20c0-4 3-6 7-6s7 2 7 6"/><line x1="17" y1="8" x2="17" y2="14"/><line x1="14" y1="11" x2="20" y2="11"/>',
    "phone": '<path d="M5 3h3l1.5 4.5-2 1.5a11 11 0 0 0 5.5 5.5l1.5-2 4.5 1.5V19a1.5 1.5 0 0 1-1.6 1.5C10.4 19.8 4.2 13.6 3.5 6.6A1.5 1.5 0 0 1 5 3z"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16,17 21,12 16,7"/><line x1="21" y1="12" x2="9" y2="12"/>',
    "download": '<path d="M12 3v12"/><polyline points="7,10 12,15 17,10"/><path d="M5 19h14"/>',
    "trash": '<polyline points="4,7 20,7"/><path d="M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7"/><polyline points="21,3 21,9 15,9"/>',
    "chevron-right": '<polyline points="9,6 15,12 9,18"/>',
    "arrow-right": '<line x1="4" y1="12" x2="20" y2="12"/><polyline points="14,6 20,12 14,18"/>',
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "bar-chart": '<line x1="6" y1="20" x2="6" y2="12"/><line x1="12" y1="20" x2="12" y2="7"/><line x1="18" y1="20" x2="18" y2="14"/>',
    "file-text": '<path d="M6 2h9l5 5v15H6z"/><line x1="9" y1="13" x2="17" y2="13"/><line x1="9" y1="17" x2="17" y2="17"/>',
    "award": '<circle cx="12" cy="8" r="6"/><polyline points="8,14 6,22 12,19 18,22 16,14"/>',
    "list-checks": '<polyline points="3,7 5,9 9,5"/><line x1="12" y1="7" x2="21" y2="7"/><polyline points="3,15 5,17 9,13"/><line x1="12" y1="17" x2="21" y2="17"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><polyline points="8,12 11,15 16,9"/>',
    "x-circle": '<circle cx="12" cy="12" r="9"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/>',
    "alert-triangle": '<path d="M12 3 2 20h20L12 3z"/><line x1="12" y1="9" x2="12" y2="14"/><line x1="12" y1="17" x2="12" y2="17.3"/>',
    "circle": '<circle cx="12" cy="12" r="9"/>',
    "send": '<line x1="21" y1="3" x2="10" y2="14"/><polygon points="21,3 14,21 10,14 3,10"/>',
    "upload": '<path d="M12 21V9"/><polyline points="7,14 12,9 17,14"/><path d="M5 5h14"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
    "layers": '<polygon points="12,3 21,8 12,13 3,8"/><polyline points="3,15 12,20 21,15"/><polyline points="3,11.5 12,16.5 21,11.5"/>',
}


def icon(name: str, size: int = 20, color: str = "currentColor", stroke: float = 2.0) -> str:
    body = _ICON_BODY.get(name, _ICON_BODY["circle"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-4px;display:inline-block;">{body}</svg>'
    )


# ── 공통 CSS ────────────────────────────────────────────────────────────────
def inject_base_css():
    render_html(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] * {{
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Rounded' !important;
    }}
    [data-testid="stAppViewContainer"] {{ background: {BRAND['bg']}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1080px; }}
    #MainMenu, footer {{ visibility: hidden; }}
    [data-testid="stExpandSidebarButton"] {{ display: none !important; }}

    h1, h2, h3 {{ color: {BRAND['ink']}; letter-spacing: -0.3px; }}

    /* ── 상단 네비게이션 바 ─────────────────────────────────────────────── */
    .sw-navbar {{
        display:flex; align-items:center; justify-content:space-between;
        background:{BRAND['card']}; border:1px solid {BRAND['border']};
        border-radius:18px; padding:12px 22px; margin-bottom:22px;
        box-shadow:0 4px 18px rgba(34,30,31,0.05);
    }}
    .sw-navbar img {{ height:26px; display:block; }}
    .sw-navbar-right {{ display:flex; align-items:center; gap:10px; }}
    .sw-chip {{
        font-size:0.78rem; font-weight:700; color:{BRAND['teal']};
        background:rgba(57,188,165,0.12); padding:5px 13px; border-radius:20px;
        display:inline-flex; align-items:center; gap:5px; white-space:nowrap;
    }}
    .sw-chip.admin {{ color:{BRAND['coral']}; background:rgba(241,88,53,0.12); }}

    /* ── 페이지 헤더 ────────────────────────────────────────────────────── */
    .sw-page-header {{ display:flex; align-items:center; gap:16px; margin: 6px 0 22px 0; }}
    .sw-icon-badge {{
        min-width:48px; width:48px; height:48px; border-radius:15px;
        background:linear-gradient(135deg, {BRAND['coral']}, {BRAND['orange']});
        display:flex; align-items:center; justify-content:center; color:#fff;
        box-shadow:0 8px 18px rgba(241,88,53,0.28); flex-shrink:0;
    }}
    .sw-page-header h1 {{ font-size:1.55rem; font-weight:800; margin:0; }}
    .sw-page-header p {{ font-size:0.92rem; color:{BRAND['muted']}; margin:3px 0 0 0; }}

    /* ── 카드 ──────────────────────────────────────────────────────────── */
    .sw-card {{
        background:{BRAND['card']}; border:1px solid {BRAND['border']};
        border-radius:18px; padding:22px 24px; box-shadow:0 4px 16px rgba(34,30,31,0.04);
        margin-bottom:16px;
    }}
    .sw-info-strip {{ display:flex; gap:12px; flex-wrap:wrap; margin:18px 0; }}
    .sw-info-pill {{
        flex:1; min-width:150px; background:{BRAND['card']}; border:1px solid {BRAND['border']};
        border-radius:14px; padding:14px 16px; display:flex; align-items:center; gap:10px;
        box-shadow:0 2px 10px rgba(34,30,31,0.03);
    }}
    .sw-info-pill .ic {{
        width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
        background:rgba(57,188,165,0.12); color:{BRAND['teal']}; flex-shrink:0;
    }}
    .sw-info-pill .txt b {{ display:block; font-size:0.95rem; color:{BRAND['ink']}; }}
    .sw-info-pill .txt span {{ font-size:0.78rem; color:{BRAND['muted']}; }}

    /* ── 버튼 ──────────────────────────────────────────────────────────── */
    .stButton>button, [data-testid="stFormSubmitButton"]>button, [data-testid="stDownloadButton"]>button {{
        border-radius:12px !important; font-weight:700 !important;
        transition: transform .15s, box-shadow .15s, filter .15s !important;
    }}
    [data-testid="stFormSubmitButton"]>button, .stButton>button[kind="primary"] {{
        background:linear-gradient(90deg, {BRAND['coral']}, {BRAND['orange']}) !important;
        border:none !important; color:#fff !important;
        box-shadow:0 8px 20px rgba(241,88,53,0.28) !important;
    }}
    [data-testid="stFormSubmitButton"]>button:hover, .stButton>button[kind="primary"]:hover {{
        filter:brightness(1.05) !important; transform:translateY(-1px) !important;
    }}
    .stButton>button[kind="secondary"] {{
        background:{BRAND['card']} !important; border:1.5px solid {BRAND['border']} !important;
        color:{BRAND['ink']} !important;
    }}
    .stButton>button[kind="secondary"]:hover {{
        border-color:{BRAND['teal']} !important; color:{BRAND['teal']} !important;
    }}

    /* ── 네비게이션 카드 버튼 (홈 화면 전용, .st-key-home_nav_row로 범위 한정) ── */
    .st-key-home_nav_row [data-testid="stBaseButton-secondary"] {{
        background:{BRAND['card']} !important; border:1.5px solid {BRAND['border']} !important;
        border-radius:18px !important; padding:26px 18px !important; color:{BRAND['ink']} !important;
        font-size:1rem !important; font-weight:700 !important; min-height:108px !important;
        white-space:pre-line !important; line-height:1.75 !important; text-align:left !important;
        box-shadow:0 4px 14px rgba(34,30,31,0.04) !important;
        transition: all .18s !important;
    }}
    .st-key-home_nav_row [data-testid="stBaseButton-secondary"]:hover {{
        border-color:{BRAND['teal']} !important; transform:translateY(-2px) !important;
        box-shadow:0 10px 24px rgba(57,188,165,0.18) !important;
    }}
    .st-key-home_nav_row [data-testid="stBaseButton-primary"] {{
        background:linear-gradient(135deg, {BRAND['coral']}, {BRAND['orange']}) !important;
        border:none !important; border-radius:18px !important; padding:26px 18px !important;
        color:#fff !important; font-size:1rem !important; font-weight:700 !important;
        min-height:108px !important; white-space:pre-line !important; line-height:1.75 !important;
        text-align:left !important; box-shadow:0 10px 24px rgba(241,88,53,0.32) !important;
        transition: all .18s !important;
    }}
    .st-key-home_nav_row [data-testid="stBaseButton-primary"]:hover {{
        transform:translateY(-2px) !important; box-shadow:0 14px 30px rgba(241,88,53,0.4) !important;
    }}

    /* ── 탭 ────────────────────────────────────────────────────────────── */
    [data-testid="stTab"] {{
        font-weight:700 !important; color:{BRAND['muted']} !important; font-size:1rem !important;
    }}
    [data-testid="stTab"][aria-selected="true"] {{ color:{BRAND['coral']} !important; }}
    [role="tablist"] {{ border-bottom:2px solid {BRAND['border']} !important; gap:6px !important; }}
    [data-testid="stTab"][aria-selected="true"] {{ border-bottom-color:{BRAND['coral']} !important; }}

    /* ── 입력 필드 ─────────────────────────────────────────────────────── */
    input[type="text"], input[type="password"], textarea, [data-baseweb="select"] > div {{
        border-radius:10px !important;
    }}
    input[type="text"]:focus, input[type="password"]:focus, textarea:focus {{
        border-color:{BRAND['teal']} !important;
        box-shadow:0 0 0 3px rgba(57,188,165,0.18) !important;
    }}

    /* ── expander / dataframe 카드화 ──────────────────────────────────── */
    [data-testid="stExpander"] {{
        border:1px solid {BRAND['border']} !important; border-radius:16px !important;
        background:{BRAND['card']} !important; box-shadow:0 2px 10px rgba(34,30,31,0.03) !important;
    }}
    [data-testid="stMetric"] {{
        background:{BRAND['card']}; border:1px solid {BRAND['border']}; border-radius:14px;
        padding:12px 14px;
    }}

    .sw-footer {{ text-align:center; margin-top:36px; color:{BRAND['muted']}; font-size:0.8rem; }}
    </style>
    """)


def navbar(user: dict | None, active: str = ""):
    """상단 네비게이션 바 (로고 + 배지). 페이지 이동 버튼은 호출부에서 별도 렌더링."""
    is_admin = bool(user and user.get("is_admin"))
    chip = ""
    if user:
        role = "관리자" if is_admin else "응시자"
        chip = f'<span class="sw-chip{" admin" if is_admin else ""}">{icon("user", 14)} {user.get("name","")} · {role}</span>'
    render_html(f"""
    <div class="sw-navbar">
        <img src="{logo_data_uri('horizontal')}" alt="상상우리" />
        <div class="sw-navbar-right">{chip}</div>
    </div>
    """)


def page_header(title: str, subtitle: str, icon_name: str = "file-text"):
    render_html(f"""
    <div class="sw-page-header">
        <div class="sw-icon-badge">{icon(icon_name, 24, "#fff")}</div>
        <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """)


def info_pill(icon_name: str, label: str, value: str) -> str:
    return (
        f'<div class="sw-info-pill">'
        f'<div class="ic">{icon(icon_name, 18)}</div>'
        f'<div class="txt"><b>{value}</b><span>{label}</span></div>'
        f'</div>'
    )


def footer():
    render_html(f"""
    <div class="sw-footer">© 주식회사 상상우리 · AI리터러시지도사 민간 자격 시험 공식 응시 플랫폼</div>
    """)

import streamlit as st
from utils.auth import login_user, register_user

st.set_page_config(
    page_title="주식회사 상상우리 | AI리터러시지도사 민간 자격 시험",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 배경 */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2d45 60%, #0d1b2a 100%);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }

/* 메인 카드 컨테이너 */
.main-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 20px;
    padding: 40px 36px 32px 36px;
    margin: 0 auto;
    max-width: 560px;
    backdrop-filter: blur(12px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
}

/* 폼/탭 영역을 감싸는 카드 */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 22px 20px 14px 20px;
}

/* 배지 */
.hero-badge {
    display: flex;
    justify-content: center;
    margin-bottom: 14px;
    filter: drop-shadow(0 6px 18px rgba(21,101,192,0.55));
}

/* 타이틀 */
.hero-company {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: #7fa8d0;
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    color: #ffffff;
    text-align: center;
    margin-bottom: 4px;
    letter-spacing: -0.5px;
    line-height: 1.3;
}
.hero-sub {
    font-size: 0.95rem;
    color: #7fa8d0;
    text-align: center;
    margin-bottom: 28px;
}

/* 로그인 필드 라벨 */
.field-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: #90caf9;
    margin: 16px 0 6px 4px;
}
.field-label:first-of-type {
    margin-top: 4px;
}

/* 환영 배너 */
.welcome-box {
    background: linear-gradient(90deg, #1565C0 0%, #1976D2 100%);
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 24px;
    text-align: center;
}
.welcome-name {
    font-size: 1.35rem;
    font-weight: 700;
    color: #ffffff;
}
.welcome-sub {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.75);
    margin-top: 2px;
}
.admin-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.4);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    color: #fff;
    margin-top: 6px;
}

/* 구분선 */
.divider-line {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 20px 0;
}

/* 네비게이션 카드 버튼 (컬럼 내부) */
[data-testid="stColumn"] [data-testid="baseButton-secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.14) !important;
    border-radius: 16px !important;
    padding: 24px 16px !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    min-height: 100px !important;
    white-space: pre-line !important;
    line-height: 1.7 !important;
    transition: all 0.2s !important;
}
[data-testid="stColumn"] [data-testid="baseButton-secondary"]:hover {
    background: rgba(21,101,192,0.35) !important;
    border-color: #42a5f5 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(21,101,192,0.4) !important;
}
[data-testid="stColumn"] [data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1565C0 0%, #1976D2 100%) !important;
    border: 1.5px solid #42a5f5 !important;
    border-radius: 16px !important;
    padding: 24px 16px !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    min-height: 100px !important;
    box-shadow: 0 4px 14px rgba(21,101,192,0.45) !important;
    white-space: pre-line !important;
    line-height: 1.7 !important;
    transition: all 0.2s !important;
}
[data-testid="stColumn"] [data-testid="baseButton-primary"]:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1e88e5 100%) !important;
    box-shadow: 0 6px 22px rgba(21,101,192,0.6) !important;
}

/* 로그아웃 버튼 */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

/* 탭 스타일 */
button[data-baseweb="tab"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #90caf9 !important;
}
button[aria-selected="true"][data-baseweb="tab"] {
    color: #ffffff !important;
    border-bottom-color: #1565C0 !important;
}

/* 입력 필드 */
input[type="text"], input[type="password"] {
    border-radius: 10px !important;
    border-color: rgba(255,255,255,0.15) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
input[type="text"]:focus, input[type="password"]:focus {
    border-color: #42a5f5 !important;
    box-shadow: 0 0 0 3px rgba(66,165,245,0.25) !important;
}

/* 로그인 버튼 */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(90deg, #1565C0, #1976D2) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 12px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(90deg, #1976D2, #1e88e5) !important;
    box-shadow: 0 4px 14px rgba(21,101,192,0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session init ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ── Already logged in ─────────────────────────────────────────────────────────
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    is_admin = user.get("is_admin", False)

    # 환영 배너
    admin_badge = '<span class="admin-badge">⚙️ 관리자</span>' if is_admin else ""
    st.markdown(f"""
    <div class="welcome-box">
        <div class="welcome-name">👋 {user['name']}님, 환영합니다!</div>
        <div class="welcome-sub">주식회사 상상우리 · AI리터러시지도사 민간 자격 시험</div>
        {admin_badge}
    </div>
    """, unsafe_allow_html=True)

    # 네비게이션 버튼
    if is_admin:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✏️\n시험 응시하기\n자격시험 시작", key="nav_exam", use_container_width=True, type="primary"):
                st.switch_page("pages/1_exam.py")
        with c2:
            if st.button("📋\n내 결과 보기\n점수 및 합격 확인", key="nav_results", use_container_width=True):
                st.switch_page("pages/2_results.py")
        with c3:
            if st.button("📊\n관리자 패널\n채점 및 결과 관리", key="nav_admin", use_container_width=True):
                st.switch_page("pages/3_admin.py")
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✏️\n시험 응시하기\n자격시험 시작", key="nav_exam", use_container_width=True, type="primary"):
                st.switch_page("pages/1_exam.py")
        with c2:
            if st.button("📋\n내 결과 보기\n점수 및 합격 확인", key="nav_results", use_container_width=True):
                st.switch_page("pages/2_results.py")

    # 시험 안내 요약
    st.markdown("""
    <hr class="divider-line">
    <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:16px;">
        <span style="color:#90caf9; font-size:0.85rem;">🕐 제한시간 90분</span>
        <span style="color:#90caf9; font-size:0.85rem;">📝 총 80문제</span>
        <span style="color:#90caf9; font-size:0.85rem;">🎯 평균 60점 이상 합격</span>
        <span style="color:#90caf9; font-size:0.85rem;">📚 4개 분야</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 로그아웃", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# ── Login / Register ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 28px 0 8px 0;">
    <div class="hero-badge">
        <svg width="88" height="88" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="badgeGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#42a5f5"/>
                    <stop offset="100%" stop-color="#1565C0"/>
                </linearGradient>
            </defs>
            <circle cx="48" cy="44" r="40" fill="url(#badgeGrad)" stroke="rgba(255,255,255,0.35)" stroke-width="2"/>
            <text x="48" y="52" font-family="'Segoe UI', Arial, sans-serif" font-size="26" font-weight="800" fill="#ffffff" text-anchor="middle">AI</text>
            <path d="M22 76 L48 64 L74 76 L64 92 L48 84 L32 92 Z" fill="#ffd54f"/>
            <circle cx="48" cy="44" r="40" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>
        </svg>
    </div>
    <div class="hero-company">주식회사 상상우리</div>
    <div class="hero-title">AI리터러시지도사<br>민간 자격 시험</div>
    <div class="hero-sub">자격시험 응시 플랫폼</div>
</div>
""", unsafe_allow_html=True)

tab_login, tab_register = st.tabs(["🔑  로그인", "📝  회원가입"])

with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown('<div class="field-label">이메일</div>', unsafe_allow_html=True)
        email = st.text_input("이메일", placeholder="example@email.com", label_visibility="collapsed")
        st.markdown('<div class="field-label">패스워드</div>', unsafe_allow_html=True)
        password = st.text_input("패스워드", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("이메일과 비밀번호를 입력해주세요.")
        else:
            with st.spinner("로그인 중..."):
                user = login_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("register_form"):
        r_name     = st.text_input("이름 *", placeholder="홍길동")
        r_email    = st.text_input("이메일 *", placeholder="example@email.com")
        r_phone    = st.text_input("연락처 *", placeholder="010-0000-0000")
        r_password = st.text_input("비밀번호 * (6자 이상)", type="password", placeholder="비밀번호")
        r_confirm  = st.text_input("비밀번호 확인 *", type="password", placeholder="비밀번호 재입력")
        reg_submitted = st.form_submit_button("회원가입", use_container_width=True, type="primary")

    if reg_submitted:
        if not all([r_name, r_email, r_phone, r_password, r_confirm]):
            st.error("모든 항목을 입력해주세요.")
        elif r_password != r_confirm:
            st.error("비밀번호가 일치하지 않습니다.")
        elif len(r_password) < 6:
            st.error("비밀번호는 6자 이상이어야 합니다.")
        else:
            with st.spinner("가입 중..."):
                ok, msg = register_user(r_name, r_email, r_phone, r_password)
            if ok:
                st.success("✅ 회원가입 완료! 로그인 탭에서 로그인해주세요.")
            else:
                st.error(msg)

# 하단 안내
st.markdown("""
<div style="text-align:center; margin-top:32px; color:rgba(255,255,255,0.3); font-size:0.78rem;">
    © 주식회사 상상우리 · AI리터러시지도사 민간 자격 시험 공식 응시 플랫폼
</div>
""", unsafe_allow_html=True)

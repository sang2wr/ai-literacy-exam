import streamlit as st
from utils.auth import login_user, register_user

st.set_page_config(
    page_title="AI리터러시지도사 자격시험",
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
}

/* 타이틀 */
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #ffffff;
    text-align: center;
    margin-bottom: 4px;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 0.95rem;
    color: #7fa8d0;
    text-align: center;
    margin-bottom: 28px;
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

/* 네비게이션 버튼 카드 */
.nav-grid {
    display: grid;
    gap: 14px;
    margin-bottom: 20px;
}
.nav-grid-3 { grid-template-columns: repeat(3, 1fr); }
.nav-grid-2 { grid-template-columns: repeat(2, 1fr); }

.nav-btn {
    display: block;
    text-decoration: none !important;
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.14);
    border-radius: 16px;
    padding: 22px 16px 18px 16px;
    text-align: center;
    transition: all 0.2s;
    cursor: pointer;
}
.nav-btn:hover {
    background: rgba(21,101,192,0.35);
    border-color: #42a5f5;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(21,101,192,0.4);
}
.nav-btn-primary {
    background: linear-gradient(135deg, #1565C0 0%, #1976D2 100%);
    border-color: #42a5f5;
    box-shadow: 0 4px 14px rgba(21,101,192,0.45);
}
.nav-btn-primary:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1e88e5 100%);
    box-shadow: 0 6px 22px rgba(21,101,192,0.6);
}
.nav-icon { font-size: 2rem; margin-bottom: 8px; }
.nav-label {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    display: block;
    margin-bottom: 3px;
}
.nav-desc {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.6);
    display: block;
}

/* 구분선 */
.divider-line {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 20px 0;
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
        <div class="welcome-sub">AI리터러시지도사 자격시험 플랫폼</div>
        {admin_badge}
    </div>
    """, unsafe_allow_html=True)

    # 네비게이션 버튼
    if is_admin:
        st.markdown("""
        <div class="nav-grid nav-grid-3">
            <a class="nav-btn nav-btn-primary" href="/1_시험보기" target="_self">
                <div class="nav-icon">✏️</div>
                <span class="nav-label">시험 응시하기</span>
                <span class="nav-desc">자격시험 시작</span>
            </a>
            <a class="nav-btn" href="/2_내결과" target="_self">
                <div class="nav-icon">📋</div>
                <span class="nav-label">내 결과 보기</span>
                <span class="nav-desc">점수 및 합격 확인</span>
            </a>
            <a class="nav-btn" href="/3_관리자패널" target="_self">
                <div class="nav-icon">📊</div>
                <span class="nav-label">관리자 패널</span>
                <span class="nav-desc">채점 및 결과 관리</span>
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="nav-grid nav-grid-2">
            <a class="nav-btn nav-btn-primary" href="/1_시험보기" target="_self">
                <div class="nav-icon">✏️</div>
                <span class="nav-label">시험 응시하기</span>
                <span class="nav-desc">자격시험 시작</span>
            </a>
            <a class="nav-btn" href="/2_내결과" target="_self">
                <div class="nav-icon">📋</div>
                <span class="nav-label">내 결과 보기</span>
                <span class="nav-desc">점수 및 합격 확인</span>
            </a>
        </div>
        """, unsafe_allow_html=True)

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
<div style="text-align:center; padding: 32px 0 8px 0;">
    <div style="font-size:3rem; margin-bottom:8px;">🤖</div>
    <div class="hero-title">AI리터러시지도사</div>
    <div class="hero-sub">자격시험 응시 플랫폼</div>
</div>
""", unsafe_allow_html=True)

tab_login, tab_register = st.tabs(["🔑  로그인", "📝  회원가입"])

with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="example@email.com", label_visibility="collapsed")
        st.caption("이메일")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        st.caption("비밀번호")
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
    AI리터러시지도사 자격시험 공식 응시 플랫폼
</div>
""", unsafe_allow_html=True)

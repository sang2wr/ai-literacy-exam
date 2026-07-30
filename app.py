import streamlit as st
from utils.auth import login_user, register_user
from utils.theme import inject_base_css, navbar, icon, info_pill, footer, logo_data_uri, logo_path, BRAND, render_html

st.set_page_config(
    page_title="주식회사 상상우리 | AI리터러시지도사 민간 자격 시험",
    page_icon=logo_path("icon"),
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_base_css()

render_html(f"""
<style>
.sw-hero {{
    background: radial-gradient(circle at 15% 20%, rgba(241,88,53,0.35), transparent 45%),
                radial-gradient(circle at 85% 15%, rgba(57,188,165,0.30), transparent 45%),
                linear-gradient(160deg, {BRAND['ink']} 0%, #322C2D 100%);
    border-radius: 24px;
    padding: 44px 32px 34px 32px;
    text-align: center;
    box-shadow: 0 20px 50px rgba(34,30,31,0.22);
    margin-bottom: 18px;
}}
.sw-hero img.sw-hero-logo {{ height: 46px; margin-bottom: 18px; }}
.sw-hero-eyebrow {{
    font-size: 0.8rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,0.55); margin-bottom: 10px;
}}
.sw-hero-title {{ font-size: 1.85rem; font-weight: 800; color: #fff; line-height: 1.35; margin-bottom: 8px; letter-spacing: -0.5px; }}
.sw-hero-sub {{ font-size: 0.95rem; color: rgba(255,255,255,0.68); }}

.field-label {{ font-size: 0.82rem; font-weight: 700; color: {BRAND['ink_soft']}; margin: 14px 0 6px 4px; }}
.field-label:first-of-type {{ margin-top: 2px; }}

.welcome-box {{
    background: linear-gradient(120deg, {BRAND['coral']} 0%, {BRAND['orange']} 100%);
    border-radius: 20px; padding: 26px 28px; margin-bottom: 6px; color: #fff;
    display:flex; align-items:center; gap:18px; box-shadow: 0 14px 30px rgba(241,88,53,0.28);
}}
.welcome-avatar {{
    width:56px; height:56px; border-radius:16px; background:rgba(255,255,255,0.22);
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.welcome-name {{ font-size: 1.3rem; font-weight: 800; }}
.welcome-sub {{ font-size: 0.85rem; opacity: 0.9; margin-top: 2px; }}
</style>
""")

# ── Session init ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ── Already logged in ─────────────────────────────────────────────────────────
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    is_admin = user.get("is_admin", False)

    navbar(user)

    role_txt = "관리자 계정으로 로그인되었습니다" if is_admin else "AI리터러시지도사 자격시험 응시자"
    render_html(f"""
    <div class="welcome-box">
        <div class="welcome-avatar">{icon("user", 28, "#fff")}</div>
        <div>
            <div class="welcome-name">{user['name']}님, 환영합니다</div>
            <div class="welcome-sub">{role_txt}</div>
        </div>
    </div>
    """)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # 네비게이션 버튼
    with st.container(key="home_nav_row"):
        if is_admin:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✏️  시험 응시하기\n자격시험 시작하기", key="nav_exam", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_exam.py")
            with c2:
                if st.button("📋  내 결과 보기\n점수 및 합격 확인", key="nav_results", use_container_width=True):
                    st.switch_page("pages/2_results.py")
            with c3:
                if st.button("📊  관리자 패널\n채점 및 결과 관리", key="nav_admin", use_container_width=True):
                    st.switch_page("pages/3_admin.py")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏️  시험 응시하기\n자격시험 시작하기", key="nav_exam", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_exam.py")
            with c2:
                if st.button("📋  내 결과 보기\n점수 및 합격 확인", key="nav_results", use_container_width=True):
                    st.switch_page("pages/2_results.py")

    # 시험 안내 요약
    render_html(f"""
    <div class="sw-info-strip">
        {info_pill("clock", "제한시간", "90분")}
        {info_pill("book-open", "총 문항", "80문제")}
        {info_pill("target", "합격 기준", "평균 60점↑")}
        {info_pill("grid", "시험 구성", "4개 분야")}
    </div>
    """)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    footer()
    st.stop()

# ── Login / Register ──────────────────────────────────────────────────────────
render_html(f"""
<div class="sw-hero">
    <img class="sw-hero-logo" src="{logo_data_uri('white')}" alt="상상우리" />
    <div class="sw-hero-eyebrow">주식회사 상상우리</div>
    <div class="sw-hero-title">AI리터러시지도사<br>민간 자격 시험</div>
    <div class="sw-hero-sub">자격시험 응시 플랫폼에 오신 것을 환영합니다</div>
</div>
""")

render_html(f"""
<div class="sw-info-strip">
    {info_pill("clock", "제한시간", "90분")}
    {info_pill("book-open", "총 문항", "80문제")}
    {info_pill("target", "합격 기준", "평균 60점↑")}
    {info_pill("grid", "시험 구성", "4개 분야")}
</div>
""")

st.markdown('<div class="sw-card">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

footer()

import streamlit as st
from utils.auth import login_user, register_user

st.set_page_config(
    page_title="AI리터러시지도사 자격시험",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session init ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ── Already logged in ─────────────────────────────────────────────────────────
if st.session_state.logged_in and st.session_state.user:
    user = st.session_state.user
    st.title("🤖 AI리터러시지도사 자격시험")
    st.success(f"환영합니다, **{user['name']}**님! 로그인되었습니다.")

    if user.get("is_admin"):
        st.info("관리자 계정입니다.")
        st.page_link("pages/3_관리자패널.py", label="📊 관리자 패널로 이동", icon="📊")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.page_link("pages/1_시험보기.py", label="✏️ 시험 응시하기", icon="✏️")
        with col2:
            st.page_link("pages/2_내결과.py", label="📋 내 결과 보기", icon="📋")

    st.divider()
    if st.button("🚪 로그아웃"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# ── Login / Register ──────────────────────────────────────────────────────────
st.title("🤖 AI리터러시지도사 자격시험")
st.caption("AI리터러시지도사 자격 시험 응시 플랫폼")
st.divider()

tab_login, tab_register = st.tabs(["🔑 로그인", "📝 회원가입"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="example@email.com")
        password = st.text_input("비밀번호", type="password")
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
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 올바르지 않습니다.")

with tab_register:
    with st.form("register_form"):
        r_name     = st.text_input("이름 *")
        r_email    = st.text_input("이메일 *", placeholder="example@email.com")
        r_phone    = st.text_input("연락처 *", placeholder="010-0000-0000")
        r_password = st.text_input("비밀번호 * (6자 이상)", type="password")
        r_confirm  = st.text_input("비밀번호 확인 *", type="password")
        reg_submitted = st.form_submit_button("회원가입", use_container_width=True, type="primary")

    if reg_submitted:
        if not all([r_name, r_email, r_phone, r_password, r_confirm]):
            st.error("모든 항목을 입력해주세요.")
        elif r_password != r_confirm:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            with st.spinner("가입 중..."):
                ok, msg = register_user(r_name, r_email, r_phone, r_password)
            if ok:
                st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인해주세요.")
            else:
                st.error(msg)

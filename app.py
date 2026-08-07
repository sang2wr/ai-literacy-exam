import streamlit as st
from utils.auth import login_user, register_user
from utils.theme import inject_base_css, navbar, font_scale_control, icon, info_pill, footer, logo_data_uri, logo_path, BRAND, render_html

st.set_page_config(
    page_title="주식회사 상상우리 | AI리터러시지도사 민간 자격 시험",
    page_icon=logo_path("icon"),
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_base_css()
font_scale_control()

render_html(f"""
<style>
.sw-hero {{
    background: linear-gradient(175deg, {BRAND['ink']} 0%, #2B2627 100%);
    border-top: 6px solid {BRAND['coral']};
    border-radius: 22px;
    padding: 56px 40px 44px 40px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(20,18,18,0.06), 0 20px 44px rgba(20,18,18,0.18);
    margin-bottom: 24px;
}}
.sw-hero img.sw-hero-logo {{ height: 96px; margin-bottom: 26px; }}
.sw-hero-eyebrow {{
    font-size: 0.9rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase;
    color: {BRAND['orange']}; margin-bottom: 14px;
}}
.sw-hero-title {{
    font-family: 'Noto Serif KR', 'Pretendard', serif;
    font-size: 2.9rem; font-weight: 800; color: #fff; line-height: 1.3;
    margin-bottom: 14px; letter-spacing: -0.3px;
}}
.sw-hero-sub {{ font-size: 1.1rem; color: rgba(255,255,255,0.72); font-weight: 500; }}

.field-label {{ font-size: 0.92rem; font-weight: 700; color: {BRAND['ink_soft']}; margin: 18px 0 7px 4px; }}
.field-label:first-of-type {{ margin-top: 2px; }}

.welcome-box {{
    background: {BRAND['coral']};
    border-radius: 18px; padding: 28px 32px; margin-bottom: 6px;
    display:flex; align-items:center; gap:20px;
    box-shadow:0 10px 26px rgba(241,88,53,0.3);
}}
.welcome-avatar {{
    width:64px; height:64px; border-radius:16px; background:rgba(255,255,255,0.18);
    color:#fff;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}}
.welcome-name {{ font-size: 1.5rem; font-weight: 800; color:#fff; }}
.welcome-sub {{ font-size: 0.98rem; color:rgba(255,255,255,0.85); margin-top: 3px; font-weight: 600; }}

/* ── 랜딩 화면 전용: 아이콘 메뉴줄 ─────────────────────────────────────── */
.sw-landing-nav {{
    display:flex; gap:14px; flex-wrap:wrap; justify-content:center;
    margin: 6px 0 26px 0;
}}
.sw-landing-nav a {{
    display:flex; flex-direction:column; align-items:center; gap:8px;
    text-decoration:none; min-width:104px; padding:16px 10px;
    background:{BRAND['card']}; border:1px solid {BRAND['border']}; border-radius:16px;
    box-shadow:0 2px 4px rgba(20,18,18,0.03);
    transition: border-color .15s, transform .15s, box-shadow .15s;
}}
.sw-landing-nav a:hover {{
    border-color:{BRAND['coral']}; transform:translateY(-2px);
    box-shadow:0 10px 22px rgba(241,88,53,0.14);
}}
.sw-landing-nav a .ic {{
    width:44px; height:44px; border-radius:12px; background:rgba(241,88,53,0.08);
    color:{BRAND['coral']}; display:flex; align-items:center; justify-content:center;
}}
.sw-landing-nav a span.lbl {{ font-size:0.9rem; font-weight:700; color:{BRAND['ink']}; }}

/* ── 랜딩 화면 전용: 2단 정적 히어로 (텍스트 좌 / 그래픽 우) ───────────── */
.sw-hero2 {{
    display:flex; align-items:center; justify-content:space-between; gap:32px;
    background: linear-gradient(175deg, {BRAND['ink']} 0%, #2B2627 100%);
    border-top: 6px solid {BRAND['coral']};
    border-radius: 22px; padding: 52px 44px;
    box-shadow: 0 2px 4px rgba(20,18,18,0.06), 0 20px 44px rgba(20,18,18,0.18);
    margin-bottom: 22px;
}}
.sw-hero2-left {{ flex:1; min-width:280px; }}
.sw-hero2-eyebrow {{
    font-size: 0.9rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase;
    color: {BRAND['orange']}; margin-bottom: 14px;
}}
.sw-hero2-title {{
    font-family: 'Noto Serif KR', 'Pretendard', serif;
    font-size: 2.5rem; font-weight: 800; color: #fff; line-height: 1.32;
    margin-bottom: 14px; letter-spacing: -0.3px;
}}
.sw-hero2-sub {{ font-size: 1.05rem; color: rgba(255,255,255,0.72); font-weight: 500; margin-bottom: 26px; }}
.sw-hero2-graphic {{
    flex-shrink:0; width:180px; height:180px; border-radius:50%;
    background: radial-gradient(circle at 35% 30%, rgba(241,88,53,0.35), rgba(241,88,53,0.08) 70%);
    border: 1.5px solid rgba(255,255,255,0.14);
    display:flex; align-items:center; justify-content:center;
}}
a.sw-cta-link {{
    display:inline-flex; align-items:center; gap:10px; text-decoration:none;
    background:{BRAND['coral']}; color:#fff !important; font-weight:800; font-size:1.05rem;
    padding:16px 28px; border-radius:14px;
    box-shadow:0 10px 26px rgba(241,88,53,0.35);
    transition: filter .15s, transform .15s;
}}
a.sw-cta-link:hover {{ filter:brightness(1.06); transform:translateY(-1px); }}

/* ── 랜딩 화면 전용: 컬러 카드 3종 ─────────────────────────────────────── */
.sw-feature-row {{ display:flex; gap:18px; flex-wrap:wrap; margin: 8px 0 30px 0; }}
.sw-feature-card {{
    flex:1; min-width:230px; scroll-margin-top: 24px;
    background:{BRAND['card']}; border:1px solid {BRAND['border']};
    border-top: 5px solid var(--accent); border-radius:18px; padding:24px 22px;
    box-shadow:0 2px 4px rgba(20,18,18,0.03), 0 8px 20px rgba(20,18,18,0.04);
}}
.sw-feature-card .ic {{
    width:46px; height:46px; border-radius:13px; background:var(--accent-soft); color:var(--accent);
    display:flex; align-items:center; justify-content:center; margin-bottom:14px;
}}
.sw-feature-card h3 {{ font-size:1.15rem; font-weight:800; margin:0 0 8px 0; color:{BRAND['ink']}; }}
.sw-feature-card p {{ font-size:0.95rem; color:{BRAND['muted']}; line-height:1.6; margin:0; }}

#verify {{ scroll-margin-top: 24px; }}
.sw-verify-heading {{ text-align:center; margin: 6px 0 18px 0; }}
.sw-verify-heading h2 {{ font-size:1.5rem; font-weight:800; color:{BRAND['ink']}; margin:0 0 6px 0; }}
.sw-verify-heading p {{ font-size:0.98rem; color:{BRAND['muted']}; margin:0; }}
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
        <div class="welcome-avatar">{icon("user", 30, "#fff")}</div>
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
                if st.button("시험 응시하기", key="nav_exam", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_exam.py")
            with c2:
                if st.button("내 결과 보기", key="nav_results", use_container_width=True):
                    st.switch_page("pages/2_results.py")
            with c3:
                if st.button("관리자 패널", key="nav_admin", use_container_width=True):
                    st.switch_page("pages/3_admin.py")
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("시험 응시하기", key="nav_exam", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_exam.py")
            with c2:
                if st.button("내 결과 보기", key="nav_results", use_container_width=True):
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
    if st.button("로그아웃", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    footer()
    st.stop()

# ── Login / Register (랜딩) ──────────────────────────────────────────────────
navbar(None)

render_html(f"""
<div class="sw-hero2">
    <div class="sw-hero2-left">
        <div class="sw-hero2-eyebrow">주식회사 상상우리</div>
        <div class="sw-hero2-title">AI리터러시지도사<br>민간 자격 시험</div>
        <div class="sw-hero2-sub">4개 분야 · 총 80문제로 AI 리터러시 지도 역량을 검증하는 공식 자격시험입니다.</div>
        <a class="sw-cta-link" href="#verify">{icon("shield", 20, "#fff")} 지금 본인인증하고 응시하기</a>
    </div>
    <div class="sw-hero2-graphic">{icon("award", 76, "#F15835", 1.4)}</div>
</div>
""")

render_html(f"""
<div class="sw-landing-nav">
    <a href="#intro"><span class="ic">{icon("file-text", 20)}</span><span class="lbl">시험 소개</span></a>
    <a href="#criteria"><span class="ic">{icon("target", 20)}</span><span class="lbl">합격 기준</span></a>
    <a href="#guide"><span class="ic">{icon("list-checks", 20)}</span><span class="lbl">응시 안내</span></a>
    <a href="#verify"><span class="ic">{icon("shield", 20)}</span><span class="lbl">본인인증</span></a>
</div>
""")

render_html(f"""
<div class="sw-feature-row">
    <div id="intro" class="sw-feature-card" style="--accent:{BRAND['coral']}; --accent-soft:rgba(241,88,53,0.08);">
        <div class="ic">{icon("file-text", 22)}</div>
        <h3>시험 소개</h3>
        <p>AI 개념 이해 · AI와 문제해결 · AI 도구 및 플랫폼 사용 · 지도 계획안 작성, 4개 분야 총 80문제(객관식 72 + 주관식 8)로 구성됩니다. 제한시간은 90분이며 시간 초과 시 자동 제출됩니다.</p>
    </div>
    <div id="criteria" class="sw-feature-card" style="--accent:{BRAND['teal']}; --accent-soft:rgba(57,188,165,0.1);">
        <div class="ic">{icon("target", 22)}</div>
        <h3>합격 기준</h3>
        <p>4개 분야 평균 60점 이상 + 모든 분야 50점 이상 획득 시 필기 합격입니다. 어느 한 분야라도 50점 미만이면 필기 탈락 처리됩니다. 필기 합격자에 한해 실기 심사가 진행됩니다.</p>
    </div>
    <div id="guide" class="sw-feature-card" style="--accent:{BRAND['orange']}; --accent-soft:rgba(247,142,29,0.1);">
        <div class="ic">{icon("list-checks", 22)}</div>
        <h3>응시 안내</h3>
        <p>회원가입 후 이메일/비밀번호로 본인인증을 마치면 바로 응시할 수 있습니다. 아래 "본인인증" 영역에서 로그인 또는 회원가입을 진행해주세요.</p>
    </div>
</div>
""")

render_html("""
<div class="sw-verify-heading">
    <h2>본인 인증</h2>
    <p>로그인 또는 회원가입 후 시험에 응시할 수 있습니다.</p>
</div>
""")

st.markdown('<div id="verify"><div class="sw-card">', unsafe_allow_html=True)
tab_login, tab_register = st.tabs(["로그인", "회원가입"])

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
                st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")
            else:
                st.error(msg)
st.markdown('</div></div>', unsafe_allow_html=True)

footer()

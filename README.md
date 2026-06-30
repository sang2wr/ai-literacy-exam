# AI리터러시지도사 자격시험 플랫폼

## 배포 순서

### 1단계 — Supabase 설정

1. [supabase.com](https://supabase.com) 에 접속 → **Start your project** 클릭
2. GitHub 계정으로 가입 후 새 프로젝트 생성
3. 왼쪽 메뉴 **SQL Editor** → `setup.sql` 파일 내용 전체 붙여넣고 **Run** 실행
4. 왼쪽 메뉴 **Settings → API** 에서
   - `Project URL` → 복사
   - `anon public` 키 → 복사

### 2단계 — secrets.toml 파일 생성

`.streamlit/secrets.toml.example` 파일을 복사하여 `.streamlit/secrets.toml` 로 저장한 뒤, 위에서 복사한 값으로 교체합니다.

```toml
[supabase]
url = "https://xxxxxxxxxx.supabase.co"
anon_key = "eyJhbGciOi..."
```

### 3단계 — Streamlit Cloud 배포

1. 이 프로젝트를 **GitHub 저장소**에 올립니다 (`.streamlit/secrets.toml` 은 `.gitignore` 에 포함)
2. [share.streamlit.io](https://share.streamlit.io) 접속 → New app
3. GitHub 저장소 연결 → `app.py` 선택 → Deploy
4. **Settings → Secrets** 에서 `secrets.toml` 내용 입력 (복붙)

### 4단계 — 관리자 계정 설정

1. 앱에서 관리자용 이메일로 일반 회원가입
2. Supabase **SQL Editor** 에서 실행:
   ```sql
   UPDATE users SET is_admin = TRUE WHERE email = '관리자이메일@domain.com';
   ```

---

## 시험 구성

| 분야 | 객관식 | 주관식 | 소계 |
|---|---|---|---|
| AI 개념 이해 | 18문제 | 2문제 | 20문제 |
| AI와 문제해결 | 18문제 | 2문제 | 20문제 |
| AI 도구 및 플랫폼 사용 | 18문제 | 2문제 | 20문제 |
| 지도 계획안 작성 | 18문제 | 2문제 | 20문제 |
| **합계** | **72문제** | **8문제** | **80문제** |

- 제한 시간: **80분** (초과 시 자동 제출)
- 채점: 객관식 자동 / 주관식·실기는 관리자 수동 채점

## 문제 교체 방법

`data/questions.json` 파일에서 문제를 직접 수정합니다.
- `"type": "mc"` — 객관식 (options 4개, correct는 0~3 인덱스)
- `"type": "sa"` — 주관식 (text만 있음)

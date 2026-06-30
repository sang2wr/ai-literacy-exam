-- Supabase SQL Editor에 붙여넣고 실행하세요.

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email        VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name         VARCHAR(100) NOT NULL,
    phone        VARCHAR(20),
    is_admin     BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 시험 테이블
CREATE TABLE IF NOT EXISTS exams (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id          UUID REFERENCES users(id) NOT NULL,
    started_at       TIMESTAMPTZ,
    submitted_at     TIMESTAMPTZ,
    status           VARCHAR(20) DEFAULT 'in_progress',
    mc_score         INTEGER DEFAULT 0,
    sa_score         INTEGER,
    total_score      INTEGER,
    practical_score  INTEGER,
    practical_result VARCHAR(10),
    practical_notes  TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 답안 테이블
CREATE TABLE IF NOT EXISTS answers (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    exam_id      UUID REFERENCES exams(id) NOT NULL,
    question_id  INTEGER NOT NULL,
    area_id      INTEGER NOT NULL,
    answer_text  TEXT,
    is_correct   BOOLEAN,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Row Level Security 비활성화 (서비스용 단순 설정)
ALTER TABLE users   DISABLE ROW LEVEL SECURITY;
ALTER TABLE exams   DISABLE ROW LEVEL SECURITY;
ALTER TABLE answers DISABLE ROW LEVEL SECURITY;

-- 5. 초기 관리자 계정 생성 (비밀번호는 앱에서 직접 등록 후 is_admin=true 로 변경)
-- 관리자로 지정하려면 앱에서 일반 회원가입 후 아래 SQL 실행:
-- UPDATE users SET is_admin = TRUE WHERE email = 'admin@your-domain.com';

-- 자격증 발급 테이블 추가 — Supabase SQL Editor에 붙여넣고 실행하세요.
-- (setup.sql과 같은 패턴. 기존 테이블은 건드리지 않는 순수 추가.)

CREATE TABLE IF NOT EXISTS certificates (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id    UUID REFERENCES users(id) NOT NULL,
    exam_id    UUID REFERENCES exams(id) UNIQUE NOT NULL,
    cert_no    VARCHAR(30) UNIQUE NOT NULL,
    issued_at  TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 기존 users/exams/answers 테이블과 동일하게 RLS 비활성 (서비스는 service_role_key로 접근)
ALTER TABLE certificates DISABLE ROW LEVEL SECURITY;

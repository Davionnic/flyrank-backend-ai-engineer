# Step 1 — Extracted bullets

- TITLE: messy notes — supabase-auth (BE-03)
- Auth API with FastAPI + Supabase. signup login logout protected routes Bearer JWT.
- projects/supabase-auth/
- setup gotchas i keep forgetting:
- need SUPABASE_URL + SUPABASE_KEY in .env (anon key) — never commit real creds
- for local: turn OFF "Confirm email" in Supabase Auth settings or signup hangs waiting for mail
- swagger UI can attach Bearer token for protected routes
- what it demonstrates: registration/login, JWT, protected vs public endpoints, validation/errors.
- not claiming: multi-tenant SaaS, OAuth social, refresh-token rotation productization.
- failure mode to mention honestly: without the confirm-email toggle, "it doesnt work" looks like a code bug when its a dashboard setting.
- repo path: https://github.com/Davionnic/flyrank-backend-ai-engineer/tree/main/projects/supabase-auth

# Supabase Grants — Manual Step

`supabase/*_grants.sql` (e.g. `supabase/wave2_grants.sql`) **cannot be applied via REST / `SupabaseService` / `service_role` over HTTP** — Supabase `GRANT` requires a direct Postgres connection. The file must be executed manually.

## Apply

**Option A — Supabase Dashboard (always works)**
1. Open Supabase project → SQL Editor
2. Copy-paste contents of `supabase/*_grants.sql`
3. Run

**Option B — Linked CLI (if `supabase link` is set up)**
```bash
npx supabase db execute --file supabase/wave2_grants.sql --linked
# or with DATABASE_URL
psql "$DATABASE_URL" -f supabase/wave2_grants.sql
```

## Verify

```bash
# should return rows (no 42501)
php artisan tinker --execute "app(\App\Services\SupabaseService::class)->select('category_budgets')"
# or via quickstart.md scenario in plan
```

## Tasks

In `specs/<feature>/tasks.md` split the grant work:

- `T00x [P?] Apply supabase/*_grants.sql via Dashboard / supabase db execute (manual)` — status = done after SQL Editor run
- `T00y Verify SupabaseService SELECT before/after grant (expect 42501 then OK)` — automation, confirms grant landed

Do not attempt `GRANT` via `SupabaseService` REST — it will `42501 Grant required` and is not automatable.

Ref: `research.md` / `plan.md` should tag `supabase/*_grants.sql` as **manual dashboard step**.

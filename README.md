# RegWatch

"Google Alerts for the Diário Oficial da União (DOU)" for professional-services
firms — watch arbitrary terms on behalf of many clients, get each new mention with
a one-line AI summary and a category, via a web dashboard and per-client email
digests.

Early stage. Start with the design spec:
[`docs/superpowers/specs/2026-06-26-regwatch-design.md`](docs/superpowers/specs/2026-06-26-regwatch-design.md).

Operator procedures (reindex, backfills): see [docs/runbook.md](docs/runbook.md).

Built clean-room (TDD in every layer).

## Local development

1. **Database** — start Postgres:
   ```bash
   docker compose up -d db
   ```
2. **Backend**:
   ```bash
   uv sync
   PYTHONPATH=src DJANGO_DEBUG=1 uv run python manage.py migrate
   PYTHONPATH=src DJANGO_DEBUG=1 uv run python manage.py invite_user \
     --workspace "Dev Workspace" --email dev@regwatch.local --password <choose-one>
   PYTHONPATH=src DJANGO_DEBUG=1 uv run python manage.py runserver 8000
   ```
   `invite_user` is the only way to create a login — this app is invite-only, there's
   no `createsuperuser`/public signup. Re-running it with the same `--email` just
   updates that user (safe to repeat).

   If port 8000 is already taken by something else on your machine, run on another
   port (e.g. `runserver 8010`) and see the frontend step below for the matching env var.

3. **Frontend** (separate terminal):
   ```bash
   cd web
   pnpm install
   pnpm run dev
   ```
   Vite proxies `/api` to `http://localhost:8000` by default (same-origin, so
   session cookies/CSRF work). If you ran Django on a different port, point the
   proxy at it: `VITE_API_TARGET=http://localhost:8010 pnpm run dev`.

4. Open the URL Vite prints (default `http://localhost:5173`) and log in with the
   user you created in step 2.

`docker compose stop db` / `docker compose up -d db` to pause and resume the database
between sessions without losing data (no volume is declared, so `docker compose down`
or removing the container does lose it).

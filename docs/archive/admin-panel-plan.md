# The admin panel

Archived plan (done 2026-09-23). The full text is in git history: `git log -- docs/archive/admin-panel-plan.md`.

A page on the download site (`/admin`), behind a GitHub login for `autobleem2` members: everyone may look,
the `release-managers` team may press buttons. It shows the **builds** (every queued or running workflow
run of the org, its jobs, an ETA from the median of recent successful runs, the last finished), the
**channels** (what release/testing/nightly hold, from the site's catalogs), **health** (the self-hosted
runner, the server's free disk, the image's newest tag, the last nightly) and an **audit log**. Buttons:
refresh nightly, promote (alpha/beta, rc, release), cancel/re-run a run, withdraw a testing or nightly build,
republish the page. The logic lives in workflows - autobleem-main's `nightly.yml` and `promote.yml`
(`tools/release.py`, dry run by default), autobleem-repo's `withdraw.yml` and `page.yml` - so everything the
panel does can also be done with `gh workflow run`.

**The API**: every view and button is also JSON (`GET /admin/api/status|channels|health|audit`, `POST
/admin/api/nightly|promote|runs/<repo>/<id>/cancel|rerun|withdraw|page`), for scripts and Claude sessions.
It takes `Authorization: Bearer <GitHub token>`: the service asks GitHub whose token it is and applies the
same member/release-manager rules - no separate API keys.

**How it is built**: one GitHub App, **`autobleem-admin`**, installed on the org, does both the users' login
(its OAuth flow) and the server's API calls (installation tokens); the orchestration workflows use it too
(`actions/create-github-app-token` with `AB_ADMIN_APP_ID` / `AB_ADMIN_APP_KEY`), because the default
`GITHUB_TOKEN` cannot start workflows in other repositories. oauth2-proxy does the browser login, the panel
(autobleem-repo `admin/`, Python + FastAPI) checks team membership before any action, Caddy routes
`/admin` and `/oauth2/`. Telegram and browser notifications when a run finishes or fails.

## Still open

- Telegram: a bot and chat id into the server's `admin/.env` (`AB_TELEGRAM_TOKEN`, `AB_TELEGRAM_CHAT`), then
  restart the panel (autobleem-repo `admin/README.md`).
- Confirm the org variable `AB_ADMIN_APP_ID` and secret `AB_ADMIN_APP_KEY` are set - `nightly.yml` and
  `promote.yml` cannot reach the other repositories without them.
- Masters carrying unreleased CI commits: reset before the first `release` merge, or not.
- Version 2: release notes drafted from the commits; the tester checklist's pass/fail per build.

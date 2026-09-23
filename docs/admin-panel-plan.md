# The admin panel - plan (2026-09-23)

A page on the download site, behind a GitHub login, that shows what the builders are doing and lets the
release team start builds and promotions. The owner's choices (2026-09-23): **login with GitHub, org members
only**; **viewing** for every `autobleem2` member, **buttons** for the `release-managers` team; **gitflow-lite**
promotions; notifications in the **browser** and by **Telegram**; first version = status, **channels +
health**, **cancel / re-run / logs**, **withdraw + audit log**. Later: release notes drafted from commits,
the tester checklist's pass/fail per build.

## What it shows

- **Builds**: every workflow run of the org's repositories that is queued or in progress, with its jobs, how
  long it has run and **about how long it has left** (the median of that workflow's and job's last successful
  runs), and the last finished ones with their result. Links to each run's logs. A run finishing or failing
  raises a browser notification while the page is open, and a Telegram message.
- **Channels**: what `release`, `testing` and `nightly` hold on the site now (version, date, which platforms
  and images), read from the site's own catalogs.
- **Health**: the self-hosted runner (online, busy, which job), the build server's free disk, the build
  image's newest tag and age, the nightly schedule's last run.
- **Audit log**: who pressed what, when, and what it started.

## What it does (release team only; every action asks for confirmation, a promotion twice)

| button | what runs |
|---|---|
| Refresh nightly - all / one platform | `autobleem-main`'s `nightly.yml`: each component's develop build (the ones that changed), then the appliance's nightly assembly for the platforms asked |
| Promote develop to testing (alpha / beta) | `promote.yml kind=alpha\|beta`: the next `vX.Y.Z-alphaN`/`-betaN` tag on develop's head of every component, their releases awaited, then the appliance's tag (it assembles and publishes the testing channel) |
| Promote to release candidate | `promote.yml kind=rc`: cut `release/vX.Y.Z` from develop in every component (the first rc), tag `vX.Y.Z-rcN` on it, as above |
| Release | `promote.yml kind=release`: tag `vX.Y.Z` on the release branches, merge them into master and back into develop, then the appliance's tag (the release channel) |
| Cancel / re-run a run | the GitHub API on that run |
| Withdraw a testing or nightly build | `autobleem-repo`'s `withdraw.yml` (self-hosted): the build's folder removed from the site, the catalogs and page regenerated |
| Republish the page | `autobleem-repo`'s `page.yml` |

The version a promotion will make is computed and shown before the confirmation (the next alpha/beta/rc
number of the current `X.Y.Z`; `X.Y.Z` itself is typed for the first pre-release of a new version).

The logic lives in **workflows**, not in the panel: the panel only dispatches them and shows their runs.
Everything it can do can also be done with `gh workflow run` from the command line, and every run is in
the Actions log.

## An API for scripts and Claude sessions (the owner's ask, 2026-09-23)

Everything the page shows and every button it has is also a **JSON API**, the page being only one client of
it: `GET /admin/api/status` (running and recent runs, ETA), `/channels`, `/health`, `/audit`; `POST
/admin/api/nightly`, `/promote` (with `preview` = the tag it would make, no change), `/runs/<repo>/<id>/cancel`,
`/rerun`, `/withdraw`, `/page`. A Claude session drives and monitors builds through it exactly as the owner
does in the browser - one place that knows what is running, how long it has left and what finished, instead
of polling each repository's Actions.

A script cannot do the browser's login, so the API also takes **`Authorization: Bearer <GitHub token>`**
(a user's own token - the `gh` CLI's, a fine-grained PAT): the service asks GitHub who the token belongs to
and applies the same rules - an org member reads, a `release-managers` member acts - and the audit log
records that user with "via API". No separate API keys to issue or leak; revoking the GitHub token revokes
the access. Caddy passes `/admin/api/` requests that carry a bearer token straight to the service (oauth2-
proxy handles only the browser's cookie sessions).

## How it is built

- **One GitHub App**, `autobleem-admin`, installed on the org: the users' login (its OAuth web flow) and the
  server's API calls (installation tokens). Repository permissions: Actions read/write, Contents read/write,
  Metadata read; organisation: Members read, Self-hosted runners read. The orchestration workflows use the
  same App (`actions/create-github-app-token`) - the default `GITHUB_TOKEN` cannot reach other repositories.
- **oauth2-proxy** (provider github, `--github-org=autobleem2`) does the login and the session cookie; the
  panel reads the user it passes on and checks `release-managers` membership itself before any action.
- **The panel service** (`autobleem-repo/admin/`, Python + FastAPI): the JSON API the page polls, the
  actions, the audit log (JSON lines on the server's disk), and the watcher that sends Telegram messages;
  unit tests over a fake GitHub API. The page follows autobleem-repo's page rules (the same bar, palette
  and tables).
- **Caddy** routes `/admin` and `/oauth2/` to oauth2-proxy; the public site is untouched. Three containers in
  one compose file next to the site's.

## Steps (one commit each)

0. **The owner**: create the GitHub App (the settings in `admin/README.md`) and the `release-managers` team,
   the Telegram bot and chat; put the secrets in the server's `admin/.env` and the App's id and key as org
   secrets for the workflows. Nothing below can run for real before this.
1. `autobleem-main`: `nightly.yml` and `promote.yml` (with `dry_run`, which only prints what it would tag,
   branch and merge); `autobleem-repo`: `withdraw.yml`.
2. `autobleem-repo/admin/`: the service - status, ETA, channels, health, actions, audit log - and its tests.
3. The page.
4. Telegram and browser notifications.
5. compose + Caddy; deployed on the build server, tried end to end with a dry-run promotion and a
   one-platform nightly.

## Open

- Whether the masters that carry unreleased CI commits (see `decisions.md`) are reset before the first
  `release` merge - the merge brings develop's history in either way.

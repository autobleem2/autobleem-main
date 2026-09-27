# The roadmap in the admin panel - plan (2026-09-27)

The owner's request (2026-09-27): the admin panel (`autobleem-repo/admin`,
`https://autobleem.retromenele.pl/admin/`) should show where the milestones stand and where each task is,
laid out for his convenience. Row **R27** in `docs/todo.md`. Written by Eleanor Voss - Program Manager;
built by the infrastructure team (Victor Lane).

## What the owner sees

A new **Roadmap** tab next to today's page (which becomes the **Builds** tab). The tab opens on Roadmap when
the URL is `/admin/#roadmap`, and remembers the last tab in `localStorage`. It is readable on a phone
(one column under 700 px). It has four blocks, top to bottom, most useful first:

1. **Needs you** - everything waiting on the owner, as a short list with the ID and one line each:
   - open rows whose Who column is `owner`, or whose text says it waits for the owner's decision or go;
   - the device tests waiting for him (from `status.json`, below);
   - the PM's open questions (the same file).

   This comes first because it is what he acts on.
2. **Milestones** - one card per milestone, in roadmap order: alpha2, alpha3, alpha4, beta1, rc, later. Each card has:
   - the theme and the gate (from `docs/roadmap.md`'s milestone table);
   - a progress bar: rows done out of rows done + open;
   - the open count by team.

   The next milestone (the first one not complete) is expanded; the rest are folded.
   Clicking a card filters block 4.
3. **Teams now** - one line per team, as in the PM's status block: the name, what it is working on (IDs with
   a short description), and whether it is working, waiting or asleep. Under it, the 5h/weekly usage and when
   the line was written. It comes from `status.json`.
4. **Tasks** - the todo.md table, searchable:
   - filters: milestone, team (`Team:` in the row), section (R/C/H/K/E/X/S/A/P/D), open/done;
   - each row: the ID, the bold title, size, milestone and team badges; a click unfolds the full text;
   - a done row is shown struck through, with its date and who did it.

## Where the data comes from

The panel owns no data. Everything is read from `autobleem2/autobleem-main`'s `develop` through the App's
contents API, which the panel already uses. It is cached for 60 s and refreshed with the page's existing polling.

- **`docs/todo.md`** is parsed server-side into rows `{id, section, title, text, where, size, who, ms, team,
  done, done_date, done_by}`:
  - a row is `| ID | ... |` under a `## X - ...` heading;
  - "done" means the title is `~~...~~` followed by `**done <date>**`;
  - `Team:` is taken from the text.

  Rows deleted when done (the file's rule) are no longer counted. So progress is "open" against "done and still
  listed". That is acceptable: the PM keeps done rows struck through until the milestone closes, and
  deletes them when the next milestone opens.
- **`docs/roadmap.md`** gives the milestone table (order, theme, gate).
- **`status.json`** (new, at the root of autobleem-main) holds what git does not have: the teams' current work,
  the device tests waiting, the open questions, and usage. The PM writes it with every status block she
  writes to the owner, at most every 15 minutes (a small commit, `[skip ci]`). The schema is fixed in the
  panel's tests. Without the file, blocks 1 and 3 say "no status yet".

## The API

Two new endpoints, both `GET` and read-only, open to every signed-in org member like `status`:
- `GET /admin/api/roadmap` returns `{milestones:[...], rows:[...], generated_at}`;
- `GET /admin/api/teams` returns the parsed `status.json`.

No buttons, no writes, no new App permissions (contents: read is already there).

## Build order (for the infrastructure team)

1. **A parser module** (`app/roadmap.py`) with pytest cases over a trimmed copy of today's todo.md and
   roadmap.md. The cases include a struck-through row, a row with a `|` inside backticks, a missing Team,
   and an unknown milestone.
2. **The two endpoints**, tested against the fake GitHub the existing tests use.
3. **The page**: tabs, the four blocks and the filters, in the existing `index.html` style (no framework, no
   new CDN).
4. **The `status.json` schema** and a first file written by the PM.
5. **Deploy on the build server** (`docker compose --profile admin up -d --build`, as the README says), then check
   it signed in on a desktop and a phone-width window.

The proof for "done" (`docs/debugging.md`) is the pytest run green, and a screenshot of each block from the
deployed page.

Size: M. Team: infrastructure (Victor). No owner setup is needed.

## `status.json` - schema 1 (written by the PM)

```
schema             1
written_at         ISO 8601 with the Irish offset ("2026-09-27T05:02:00+01:00")
written_by         "Eleanor Voss - Program Manager"
usage              five_hour_percent, five_hour_resets_at, weekly_percent, weekly_cap_today_percent, weekly_resets_at
teams[]            name, team, state ("working" | "waiting" | "asleep"), items[] {id, what}, note
needs_owner[]      id, kind ("decision" | "device test" | "sudo" | "question"), what
```

Unknown keys are ignored by the panel. A missing `status.json` or a `schema` other than 1 shows "no status yet".
The panel shows `written_at` as its age ("12 min ago") and greys the block past one hour.

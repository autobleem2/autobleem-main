# The admin panel in Polish (R28)

The owner, 2026-09-27: the admin panel on the site in Polish, with the information from `status.json` in
Polish too. Not a priority; the PM builds it in her free time and the infrastructure team reviews and deploys it.

## What changes

1. **The page's own text** (`autobleem-repo/admin/app/static/index.html`):
   - scope: the tabs, headings, buttons, confirmations, toasts, the "12 min ago" ages and the state names;
   - one `STRINGS = {en: {...}, pl: {...}}` table and a `t(key)` helper;
   - no library, no CDN, and the page's existing style.
   - **Polish is the default.** A PL/EN switch in the top bar is remembered in `localStorage`, wrapped in
     try/catch.
   - `<html lang>` follows the switch.
   - Numbers, commit ids, tags, file names and log lines are not translated.
2. **`status.json`, schema 1 kept**:
   - every free-text field may carry a Polish twin: `what_pl` on items and on `needs_owner` entries,
     `note_pl` on teams;
   - the page shows the `_pl` text when Polish is chosen and it is there, and falls back to the English
     one otherwise;
   - `kind` and `state` stay fixed English keys, and the page translates them (`decision` -> `decyzja`,
     `device test` -> `test na urządzeniu`, `working` -> `pracuje`, ...);
   - older readers (Wren's laptop panel) ignore the new keys;
   - the page and panel tests gain a case with `_pl` and one without.
3. **`tools/status.py`**:
   - `--item ID "what" --pl ID "co"` and `--note-pl`;
   - `needs add ... --pl "co"`;
   - the managers keep writing English, and the PM adds the Polish for the owner's queue.
   - A team that leaves out `--pl` still shows, in English.
4. **The todo task list** stays English: todo.md is the teams' working file (decisions.md: team documents
   are English). Only the page's chrome around it is Polish.

## Order

1. The strings table and the switch.
2. The `_pl` fields in the page.
3. `status.py --pl`.
4. The tests: the admin's pytest and a page check at 1280 and 390 px, as for R27.
5. Deploy on the build server.
6. Screenshots of both languages to the owner, in a question session.

Size: S-M. Team: the PM builds it; infrastructure (Victor) reviews, merges and deploys.

"""tools/status.py: closed todo rows leave status.json, the commands' edits, and the public-file guard.

    python -m unittest discover -s tests
"""
import argparse
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import status  # noqa: E402

TODO = """| ID | What |
|---|---|
| R22 | ~~**A debug driver**~~ **done 2026-09-27**: ... |
| D21 | **ci/build.sh stops dirtying the tree** ... |
| H12 | ~~done~~ ... |
| H13 | still open |
"""


def sample():
    return {"schema": 1, "teams": [
        {"name": "Victor Lane", "team": "infrastructure", "state": "working", "note": "",
         "items": [{"id": "R22", "what": "a"}, {"id": "D21", "what": "b"}]},
        {"name": "Marcus Hale", "team": "software/ui", "state": "working", "note": "",
         "items": [{"id": "H12/H13", "what": "c"}]}],
        "needs_owner": [{"id": "R22", "kind": "look", "what": "x"}, {"id": "R1", "kind": "decision", "what": "y"}]}


def run(data, *argv):
    return status.apply(argparse.Namespace(**parse(argv)), data)


def parse(argv):
    """The parsed arguments of a command, as main() would see them."""
    captured = {}
    real = status.write_and_push
    status.write_and_push = lambda args, push: captured.update(vars(args))
    try:
        status.main(list(argv))
    finally:
        status.write_and_push = real
    return captured


class ClosedRows(unittest.TestCase):
    def test_only_struck_through_rows_are_closed(self):
        self.assertEqual(status.closed_ids(TODO), {"R22", "H12"})

    def test_closed_items_and_queue_entries_go(self):
        data = sample()
        self.assertEqual(status.drop(data, status.closed_ids(TODO)), 2)
        self.assertEqual([i["id"] for i in data["teams"][0]["items"]], ["D21"])
        self.assertEqual([n["id"] for n in data["needs_owner"]], ["R1"])

    def test_a_compound_item_stays_until_every_part_is_closed(self):
        data = sample()
        status.drop(data, {"H12"})
        self.assertEqual(data["teams"][1]["items"][0]["id"], "H12/H13")
        status.drop(data, {"H12", "H13"})
        self.assertEqual(data["teams"][1]["items"], [])


class Commands(unittest.TestCase):
    def test_team_replaces_items_and_keeps_what_is_not_given(self):
        data = sample()
        run(data, "team", "Victor Lane", "--item", "D4", "the PDF", "--state", "waiting")
        t = data["teams"][0]
        self.assertEqual((t["state"], t["team"]), ("waiting", "infrastructure"))
        self.assertEqual(t["items"], [{"id": "D4", "what": "the PDF"}])

    def test_a_note_alone_leaves_the_items(self):
        data = sample()
        run(data, "team", "Victor Lane", "--note", "R22 done")
        self.assertEqual(len(data["teams"][0]["items"]), 2)
        self.assertEqual(data["teams"][0]["note"], "R22 done")

    def test_a_new_team_is_added(self):
        data = sample()
        run(data, "team", "Wren Aldercroft", "--label", "system administration", "--state", "asleep")
        self.assertEqual(data["teams"][-1]["team"], "system administration")

    def test_the_owners_queue(self):
        data = sample()
        run(data, "needs", "add", "C15", "look", "the battery icons")
        run(data, "needs", "add", "R1", "decision", "the go, again")
        self.assertEqual([n["id"] for n in data["needs_owner"]], ["R22", "C15", "R1"])
        self.assertEqual(data["needs_owner"][-1]["what"], "the go, again")
        run(data, "needs", "rm", "R22", "C15")
        self.assertEqual([n["id"] for n in data["needs_owner"]], ["R1"])

    def test_a_queue_entry_can_carry_its_howto_page(self):
        data = sample()
        run(data, "needs", "add", "R26 login", "action", "log in", "--howto", "howto/claude-login.html")
        self.assertEqual(data["needs_owner"][-1]["howto"], "howto/claude-login.html")
        for bad in ("howto/Claude.html", "../x.html", "howto/x.htm", "howto/xhtml"):
            with self.assertRaises(SystemExit):
                run(sample(), "needs", "add", "X", "action", "x", "--howto", bad)

    def test_usage(self):
        data = sample()
        run(data, "usage", "42", "59", "--cap", "70")
        self.assertEqual(data["usage"], {"five_hour_percent": 42, "weekly_percent": 59,
                                         "weekly_cap_today_percent": 70})


class PublicGuard(unittest.TestCase):
    def test_lan_addresses_and_team_paths_are_refused(self):
        for bad in ("the laptop at 192.168.68.146", "10.0.0.5", "172.20.1.1", "see _team/status/x.md"):
            with self.assertRaises(SystemExit):
                status.check_public('{"note": "%s"}' % bad)

    def test_ordinary_text_passes(self):
        status.check_public('{"note": "nightly 318, launcher d92030f, 192 px, v1.22.2"}')


if __name__ == "__main__":
    unittest.main()

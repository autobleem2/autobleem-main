"""tools/release.py: the version arithmetic, and dry runs of a promotion and a nightly over a fake GitHub.

    python -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import release  # noqa: E402


class NextTag(unittest.TestCase):
    TAGS = ["v2.0.0-alpha1", "v2.0.0-alpha2", "nightly", "r26-alpha1"]

    def test_the_next_alpha_and_the_first_beta(self):
        self.assertEqual(release.next_tag(self.TAGS, "alpha"), "v2.0.0-alpha3")
        self.assertEqual(release.next_tag(self.TAGS, "beta"), "v2.0.0-beta1")
        self.assertEqual(release.next_tag(self.TAGS + ["v2.0.0-beta1"], "beta"), "v2.0.0-beta2")

    def test_rc_and_release_of_the_version_in_progress(self):
        self.assertEqual(release.next_tag(self.TAGS, "rc"), "v2.0.0-rc1")
        self.assertEqual(release.next_tag(self.TAGS, "release"), "v2.0.0")

    def test_after_a_release_a_version_must_be_given(self):
        tags = self.TAGS + ["v2.0.0"]
        with self.assertRaises(ValueError):
            release.next_tag(tags, "alpha")
        self.assertEqual(release.next_tag(tags, "alpha", "2.1.0"), "v2.1.0-alpha1")
        with self.assertRaises(ValueError):
            release.next_tag(tags, "release", "2.0.0")  # released already

    def test_bad_version(self):
        with self.assertRaises(ValueError):
            release.next_tag(self.TAGS, "alpha", "2.1")

    def test_release_branch(self):
        self.assertEqual(release.release_branch("v2.0.0-rc2"), "release/v2.0.0")
        self.assertEqual(release.release_branch("v2.0.0"), "release/v2.0.0")


class IgnoredPaths(unittest.TestCase):
    PATTERNS = release.IGNORED_PATHS["autobleem"]

    def test_the_launchers_paths_ignore(self):
        for path in ("docs/ci.md", "docs/a/b.png", "README.md", "src/code/NOTES.md", "manuals/pl/x.md",
                     "manuals/images/pl/a.jpg"):
            self.assertTrue(release.path_ignored(path, self.PATTERNS), path)
        for path in ("src/code/app.cpp", "CMakeLists.txt", "payload/Docs/readme.txt", "tools/docs/x.py",
                     "a.mdx", "docs"):
            self.assertFalse(release.path_ignored(path, self.PATTERNS), path)

    def test_single_star_stays_in_its_folder(self):
        self.assertTrue(release.path_ignored("a/x.txt", ("a/*.txt",)))
        self.assertFalse(release.path_ignored("a/b/x.txt", ("a/*.txt",)))


class FakeGitHub(release.GitHub):
    """reads from a table; a dry run never writes"""

    def __init__(self, branches, tags, log, changed=None):
        super().__init__("token", dry_run=True, log=log)
        self.branches, self.tag_list = branches, tags
        self.changed = changed or {}  # {repo: [files between the nightly and develop]}

    def compare(self, repo, base, head):
        return {"status": "ahead", "files": [{"filename": f} for f in self.changed.get(repo, ["src/x.cpp"])]}

    def tags(self, repo):
        return self.tag_list

    def branch_sha(self, repo, branch):
        return self.branches.get((repo, branch))

    def tag_commit(self, repo, tag):
        return self.branches.get((repo, "nightly"))

    def call(self, *args, **kwargs):
        raise AssertionError("a dry run called the API: %r" % (args,))


def repos():
    return [r for stage in release.STAGES for r in stage] + [release.APPLIANCE]


class DryRuns(unittest.TestCase):
    def setUp(self):
        self.lines = []

    def test_alpha_tags_every_repository_on_develop_in_stage_order(self):
        branches = {(r, "develop"): "%040d" % i for i, r in enumerate(repos())}
        gh = FakeGitHub(branches, ["v2.0.0-alpha2"], self.lines.append)
        release.promote(gh, "alpha")
        tagged = [l.split(":")[0].replace("[dry run] ", "") for l in self.lines if " tag v2.0.0-alpha3 " in l]
        self.assertEqual(tagged, repos())
        self.assertFalse([l for l in self.lines if "merge" in l or "branch release/" in l])

    def test_rc_cuts_the_release_branch_and_release_merges_it(self):
        branches = {(r, "develop"): "%040d" % i for i, r in enumerate(repos())}
        gh = FakeGitHub(branches, ["v2.0.0-alpha2"], self.lines.append)
        release.promote(gh, "rc")
        self.assertEqual(len([l for l in self.lines if "branch release/v2.0.0 from" in l]), len(repos()))
        self.assertTrue(any(" tag v2.0.0-rc1 " in l for l in self.lines))
        self.lines.clear()
        branches.update({(r, "release/v2.0.0"): "%040d" % (i + 100) for i, r in enumerate(repos())})
        release.promote(gh, "release")
        self.assertFalse([l for l in self.lines if "branch release/" in l])  # the branch is there
        self.assertEqual(len([l for l in self.lines if "merge release/v2.0.0 into master" in l]), len(repos()))
        self.assertEqual(len([l for l in self.lines if "merge release/v2.0.0 into develop" in l]), len(repos()))

    def test_nightly_rebuilds_only_what_moved(self):
        branches = {(r, "develop"): "a" * 40 for r in release.NIGHTLY_REPOS}
        branches.update({(r, "nightly"): "a" * 40 for r in release.NIGHTLY_REPOS})
        branches[("autobleem", "develop")] = "b" * 40

        class Moved(FakeGitHub):
            def tag_commit(self, repo, tag):
                return branches[(repo, "nightly")]

        gh = Moved(branches, [], self.lines.append)
        release.nightly(gh, "psc win")
        dispatched = [l for l in self.lines if ": run " in l]
        self.assertEqual(len(dispatched), 2)
        self.assertIn("autobleem: run publish-launcher.yml on develop", dispatched[0])
        self.assertIn('assemble.yml on develop {"channel": "nightly", "platforms": "psc win", '
                      '"skip_unchanged": "true"}', dispatched[1])

    def test_nightly_takes_a_documentation_only_change_for_up_to_date(self):
        branches = {(r, "develop"): "a" * 40 for r in release.NIGHTLY_REPOS}
        branches.update({(r, "nightly"): "a" * 40 for r in release.NIGHTLY_REPOS})
        branches[("autobleem", "develop")] = "b" * 40
        branches[("ext_store", "develop")] = "c" * 40

        class Moved(FakeGitHub):
            def tag_commit(self, repo, tag):
                return branches[(repo, "nightly")]

        # the launcher moved by docs only; the Store (no paths-ignore) moved by a readme and is rebuilt
        gh = Moved(branches, [], self.lines.append,
                   changed={"autobleem": ["docs/ci.md", "CLAUDE.md"], "ext_store": ["README.md"]})
        release.nightly(gh, "psc", log=self.lines.append)
        dispatched = [l for l in self.lines if ": run " in l]
        self.assertEqual(len(dispatched), 2)
        self.assertIn("ext_store: run build.yml on develop", dispatched[0])
        self.assertTrue(any("autobleem: develop bbbbbbb is past nightly aaaaaaa by documentation only" in l
                            for l in self.lines))
        # a code change among them is a rebuild
        self.lines.clear()
        gh.changed["autobleem"] = ["docs/ci.md", "src/code/app.cpp"]
        release.nightly(gh, "psc", log=self.lines.append)
        self.assertTrue(any("autobleem: run publish-launcher.yml" in l for l in self.lines))

    def test_nightly_all_assembles_whatever_the_site_has(self):
        branches = {(r, "develop"): "a" * 40 for r in release.NIGHTLY_REPOS}
        gh = FakeGitHub(branches, [], self.lines.append)
        release.nightly(gh, "psc", rebuild_all=True)
        dispatched = [l for l in self.lines if ": run " in l]
        self.assertEqual(len(dispatched), len(release.NIGHTLY_REPOS) + 1)
        self.assertIn('"skip_unchanged": "false"', dispatched[-1])


class Waiting(unittest.TestCase):
    """wait_for_runs over a scripted run list (not a dry run - the reads are faked, nothing is written)"""

    class Runs(release.GitHub):
        def __init__(self, runs):
            super().__init__("token", log=lambda *_: None)
            self.all = runs

        def runs(self, repo, query):
            return [r for r in self.all if query == "branch=develop" or r["event"] in query]

    @staticmethod
    def make(i, event, created, conclusion):
        return {"id": i, "name": "assemble", "html_url": "u%d" % i, "event": event, "created_at": created,
                "status": "completed", "conclusion": conclusion}

    def test_a_run_replaced_in_its_concurrency_group_is_followed(self):
        gh = self.Runs([self.make(1, "workflow_dispatch", "2026-09-26T10:00:00Z", "cancelled"),
                        self.make(2, "repository_dispatch", "2026-09-26T10:01:00Z", "success")])
        release.wait_for_runs(gh, {"autobleem-appliance": ("event=workflow_dispatch", "2026-09-26T09:59:00Z")},
                              poll=0, log=lambda *_: None, superseded={"autobleem-appliance": "branch=develop"})

    def test_a_cancelled_run_nothing_replaced_fails(self):
        gh = self.Runs([self.make(1, "workflow_dispatch", "2026-09-26T10:00:00Z", "cancelled")])
        with self.assertRaises(RuntimeError):
            release.wait_for_runs(gh, {"autobleem-appliance": ("event=workflow_dispatch", "2026-09-26T09:59:00Z")},
                                  poll=0, log=lambda *_: None, superseded={"autobleem-appliance": "branch=develop"})


if __name__ == "__main__":
    unittest.main()

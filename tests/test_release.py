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


class FakeGitHub(release.GitHub):
    """reads from a table; a dry run never writes"""

    def __init__(self, branches, tags, log):
        super().__init__("token", dry_run=True, log=log)
        self.branches, self.tag_list = branches, tags

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
        self.assertIn('assemble.yml on develop {"channel": "nightly", "platforms": "psc win"}', dispatched[1])


if __name__ == "__main__":
    unittest.main()

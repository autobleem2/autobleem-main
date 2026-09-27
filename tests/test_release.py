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

    def test_r1_deleting_the_old_alpha2_tag_makes_alpha2_next_again(self):
        # R1: today's live tags (v2.0.0-alpha1, v2.0.0-alpha2) propose alpha3 - the withdrawn-and-reissued
        # promotion needs alpha2 deleted from every repo in the train (steps 7-10, not this script) first,
        # after which next_tag (reading only what still exists) yields alpha2 again on its own
        self.assertEqual(release.next_tag(["v2.0.0-alpha1", "v2.0.0-alpha2"], "alpha"), "v2.0.0-alpha3")
        self.assertEqual(release.next_tag(["v2.0.0-alpha1"], "alpha"), "v2.0.0-alpha2")


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

    def __init__(self, branches, tags, log, changed=None, latest_releases=None, compare_status=None):
        super().__init__("token", dry_run=True, log=log)
        self.branches, self.tag_list = branches, tags
        # R2: autobleem-build's master already caught up with develop by default, so a test that does not
        # care about this step sees promote() do nothing for it. setdefault (not a copy - some tests mutate
        # `branches` again after construction and expect this same gh to see it, e.g. the rc/release test)
        # only fills in the two keys when the caller did not already set them.
        self.branches.setdefault((release.BUILD_IMAGE, "develop"), "b" * 40)
        self.branches.setdefault((release.BUILD_IMAGE, "master"), self.branches[(release.BUILD_IMAGE, "develop")])
        self.changed = changed or {}  # {repo: [files between the nightly and develop]}
        self.compare_status = compare_status or {}  # {repo: "ahead"|"behind"|"identical"|"diverged"}
        # OWN_VERSION_REPOS's latest release tag, defaulted so a promote() in an unrelated test still passes
        # check_own_version_repos(); {repo: None} in a test means "no release yet"
        self.latest_releases = {"proc_unzip": "v1.1.0", "ext_store": "v1.0.1", "autobleem-themes": "v1.0.0"}
        self.latest_releases.update(latest_releases or {})

    def compare(self, repo, base, head):
        return {"status": self.compare_status.get(repo, "ahead"),
                "files": [{"filename": f} for f in self.changed.get(repo, ["src/x.cpp"])]}

    def tags(self, repo):
        return self.tag_list

    def branch_sha(self, repo, branch):
        return self.branches.get((repo, branch))

    def tag_commit(self, repo, tag):
        return self.branches.get((repo, "nightly"))

    def latest_release_tag(self, repo):
        return self.latest_releases.get(repo)

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


class ImageRebuildNeeded(unittest.TestCase):
    """image_rebuild_needed() mirrors autobleem-build's image.yml `on: push: paths:` filter - a pure function
    over a file list, no reads of its own (sync_build_image_master is what fetches the compare)."""

    def test_a_docker_file_triggers_it(self):
        self.assertTrue(release.image_rebuild_needed(["docker/Dockerfile"]))

    def test_the_workflow_file_itself_triggers_it(self):
        self.assertTrue(release.image_rebuild_needed([".github/workflows/image.yml"]))

    def test_an_unrelated_diff_does_not(self):
        self.assertFalse(release.image_rebuild_needed(["ci/build.sh", "toolchains/psc/PSCtoolchainV8.cmake"]))

    def test_no_files_does_not(self):
        self.assertFalse(release.image_rebuild_needed([]))

    def test_a_300_file_diff_is_assumed_to_need_a_rebuild(self):
        self.assertTrue(release.image_rebuild_needed(["x%d.txt" % i for i in range(300)]))


class BuildImageMaster(unittest.TestCase):
    """R2: autobleem-build's master is what every v* tag (alpha/beta/rc/release alike) compiles against
    (:latest) - promote() moves it to develop's head before tagging anything, and waits for the image build
    only when the move actually touches what image.yml rebuilds for."""

    def setUp(self):
        self.lines = []
        self.branches = {(r, "develop"): "%040d" % i for i, r in enumerate(repos())}

    def test_noop_when_master_already_matches_develop(self):
        # FakeGitHub defaults autobleem-build's master and develop to the same sha unless a test overrides -
        # this is what every unrelated test above relies on
        gh = FakeGitHub(self.branches, [], self.lines.append)
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertTrue(any("autobleem-build: master already matches develop" in l for l in self.lines))
        self.assertFalse([l for l in self.lines if "merge" in l])

    def test_no_develop_branch_raises(self):
        gh = FakeGitHub(self.branches, [], self.lines.append)
        del gh.branches[(release.BUILD_IMAGE, "develop")]
        with self.assertRaises(RuntimeError):
            release.sync_build_image_master(gh, log=self.lines.append)

    def test_a_merge_commit_makes_master_a_different_sha_but_already_caught_up(self):
        # found against the real repo while building this: master's own earlier catch-up merge gives it a
        # sha develop never has, even though it contains every commit develop does - compare() says "behind"
        # (develop is behind master) or "identical", never "ahead"/"diverged", and that - not sha equality -
        # is what must decide there is nothing to move; a plain sha check would merge on every promotion
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, [], self.lines.append,
                        compare_status={release.BUILD_IMAGE: "behind"})
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertTrue(any("already has develop" in l for l in self.lines))
        self.assertFalse([l for l in self.lines if "merge" in l or "would wait" in l])

    def test_identical_content_under_a_different_sha_is_also_a_noop(self):
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, [], self.lines.append,
                        compare_status={release.BUILD_IMAGE: "identical"})
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertTrue(any("already has develop" in l for l in self.lines))
        self.assertFalse([l for l in self.lines if "merge" in l or "would wait" in l])

    def test_diverged_still_moves_it(self):
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, [], self.lines.append,
                        compare_status={release.BUILD_IMAGE: "diverged"},
                        changed={release.BUILD_IMAGE: ["docker/Dockerfile"]})
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertIn("[dry run] autobleem-build: merge develop into master", self.lines)

    def test_moves_and_waits_when_the_diff_touches_docker(self):
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, [], self.lines.append,
                        changed={release.BUILD_IMAGE: ["docker/Dockerfile"]})
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertTrue(any("autobleem-build: master mmmmmmm is behind develop ddddddd" in l for l in self.lines))
        self.assertIn("[dry run] autobleem-build: merge develop into master", self.lines)
        self.assertTrue(any("autobleem-build: would wait for its run" in l for l in self.lines))

    def test_moves_but_does_not_wait_when_the_diff_is_unrelated(self):
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, [], self.lines.append,
                        changed={release.BUILD_IMAGE: ["ci/build.sh"]})
        release.sync_build_image_master(gh, log=self.lines.append)
        self.assertIn("[dry run] autobleem-build: merge develop into master", self.lines)
        self.assertTrue(any("no docker/image.yml change in the diff" in l for l in self.lines))
        self.assertFalse([l for l in self.lines if "would wait" in l])

    def test_promote_dry_run_moves_nothing_when_already_in_sync(self):
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append)
        release.promote(gh, "alpha", log=self.lines.append)
        self.assertFalse([l for l in self.lines if "autobleem-build: merge" in l])
        self.assertTrue(any("autobleem-build: master already matches develop" in l for l in self.lines))

    def test_promote_moves_the_build_image_before_the_first_stages_tag(self):
        self.branches[(release.BUILD_IMAGE, "develop")] = "d" * 40
        self.branches[(release.BUILD_IMAGE, "master")] = "m" * 40
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        changed={release.BUILD_IMAGE: ["docker/Dockerfile"]})
        release.promote(gh, "alpha", log=self.lines.append)
        wait_index = next(i for i, l in enumerate(self.lines)
                          if l == "[dry run] autobleem-build: would wait for its run")
        first_tag_index = next(i for i, l in enumerate(self.lines) if " tag v2.0.0-alpha3 " in l)
        self.assertLess(wait_index, first_tag_index)
        # never one of the STAGES/appliance repos itself - it gets no vX.Y.Z tag of its own
        self.assertFalse([l for l in self.lines if l.startswith("[dry run] autobleem-build: tag ")])


class OwnVersionRepos(unittest.TestCase):
    """proc_unzip, ext_store and autobleem-themes keep their own version numbers: promote() must refuse to
    start (dry run included, since the check is read-only) unless each already has a released v* version -
    it is never one of the vX.Y.Z tags this script makes."""

    def setUp(self):
        self.lines = []
        self.branches = {(r, "develop"): "%040d" % i for i, r in enumerate(repos())}

    def test_present_passes_and_is_logged(self):
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        latest_releases={"proc_unzip": "v1.1.0", "ext_store": "v1.0.1",
                                         "autobleem-themes": "v1.0.0"})
        release.check_own_version_repos(gh, log=self.lines.append)
        self.assertTrue(any("proc_unzip: keeps its own version, latest release v1.1.0" in l for l in self.lines))
        self.assertTrue(any("ext_store: keeps its own version, latest release v1.0.1" in l for l in self.lines))
        self.assertTrue(any("autobleem-themes: keeps its own version, latest release v1.0.0" in l for l in self.lines))

    def test_no_release_raises(self):
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        latest_releases={"proc_unzip": None})
        with self.assertRaises(RuntimeError):
            release.check_own_version_repos(gh, log=self.lines.append)

    def test_themes_with_no_release_yet_raises(self):
        # autobleem-themes' real state as of D5, 2026-09-27: no v* release yet
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        latest_releases={"autobleem-themes": None})
        with self.assertRaises(RuntimeError):
            release.check_own_version_repos(gh, log=self.lines.append)

    def test_a_non_v_tagged_release_raises(self):
        # GitHub's own "latest release" would never be `nightly` (that release is always marked prerelease,
        # so /releases/latest skips it) - this covers a release renamed or tagged oddly by hand
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        latest_releases={"ext_store": "release-1"})
        with self.assertRaises(RuntimeError):
            release.check_own_version_repos(gh, log=self.lines.append)

    def test_promote_refuses_before_tagging_anything_even_dry_run(self):
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append,
                        latest_releases={"proc_unzip": None})
        with self.assertRaises(RuntimeError):
            release.promote(gh, "alpha")
        # nothing was tagged - the check ran before promote() touched anything
        self.assertFalse([l for l in self.lines if " tag v" in l])

    def test_promote_never_tags_the_own_version_repos(self):
        gh = FakeGitHub(self.branches, ["v2.0.0-alpha2"], self.lines.append)
        release.promote(gh, "alpha")
        for repo in release.OWN_VERSION_REPOS:
            self.assertFalse([l for l in self.lines if l.startswith("[dry run] %s: tag " % repo)],
                             "%s must not be tagged by promote()" % repo)


class TagPrecheckGitHub(FakeGitHub):
    """FakeGitHub's own tag_commit ignores its `tag` argument (it only ever needed to answer for "nightly"
    in the existing nightly-refresh tests) - this one answers per (repo, tag) from a table, and lets a
    build's completion be scripted too, for precheck_tags()/check_existing_build()."""

    def __init__(self, branches, tags, log, existing_tags=None, runs_by_repo_tag=None, **kwargs):
        super().__init__(branches, tags, log, **kwargs)
        self.existing_tags = existing_tags or {}  # {(repo, tag): sha}
        self.runs_by_repo_tag = runs_by_repo_tag or {}  # {(repo, tag): [run, ...]}

    def tag_commit(self, repo, tag):
        return self.existing_tags.get((repo, tag))

    def runs(self, repo, query):
        # promote()/check_existing_build() only ever query "event=push&branch=<tag>"
        tag = query.split("branch=", 1)[1]
        return self.runs_by_repo_tag.get((repo, tag), [])


class TagPrecheck(unittest.TestCase):
    """R1 step 4: a tag left over from an old, withdrawn promotion (the v2.0.0-alpha2/alpha3 story) must
    never be silently re-pointed or collided with - reused only at the exact intended commit, else refused
    before anything is created."""

    def setUp(self):
        self.lines = []
        self.branches = {(r, "develop"): "%040d" % i for i, r in enumerate(repos())}

    def test_precheck_tags_reuses_a_tag_already_on_the_intended_commit(self):
        source = {r: self.branches[(r, "develop")] for r in repos()}
        gh = TagPrecheckGitHub(self.branches, [], self.lines.append,
                               existing_tags={("autobleem", "v2.0.0-alpha2"): source["autobleem"]})
        reuse = release.precheck_tags(gh, "v2.0.0-alpha2", source, repos(), log=self.lines.append)
        self.assertTrue(reuse["autobleem"])
        self.assertFalse(reuse["autobleem-appliance"])  # untouched repo: nothing to reuse, will be created
        self.assertTrue(any("autobleem: v2.0.0-alpha2 already exists on" in l for l in self.lines))

    def test_precheck_tags_stops_on_a_conflicting_commit(self):
        source = {r: self.branches[(r, "develop")] for r in repos()}
        gh = TagPrecheckGitHub(self.branches, [], self.lines.append,
                               existing_tags={("pcsx-ab", "v2.0.0-alpha2"): "f" * 40})  # not source["pcsx-ab"]
        with self.assertRaises(RuntimeError):
            release.precheck_tags(gh, "v2.0.0-alpha2", source, repos(), log=self.lines.append)

    def test_promote_stops_before_tagging_anything_on_a_conflicting_tag(self):
        # the exact R1 danger: v2.0.0-alpha2 already exists (the old, still-live tag) on a commit that is
        # not this promotion's develop head - promote() must refuse before create_tag runs for any repo
        gh = TagPrecheckGitHub(self.branches, ["v2.0.0-alpha1"], self.lines.append,
                               existing_tags={("autobleem", "v2.0.0-alpha2"): "f" * 40})
        with self.assertRaises(RuntimeError):
            release.promote(gh, "alpha", log=self.lines.append)
        self.assertFalse([l for l in self.lines if " tag v2.0.0-alpha2 " in l])

    def test_promote_reuses_a_tag_at_the_right_commit_without_recreating_it(self):
        gh = TagPrecheckGitHub(self.branches, ["v2.0.0-alpha1"], self.lines.append,
                               existing_tags={("autobleem", "v2.0.0-alpha2"): self.branches[("autobleem", "develop")]},
                               runs_by_repo_tag={("autobleem", "v2.0.0-alpha2"):
                                                 [{"status": "completed", "conclusion": "success"}]})
        release.promote(gh, "alpha", log=self.lines.append)
        self.assertFalse([l for l in self.lines if l.startswith("[dry run] autobleem: tag ")])
        self.assertTrue(any("autobleem: v2.0.0-alpha2 already exists on" in l for l in self.lines))
        # every other repo in autobleem's stage is still tagged normally
        self.assertTrue(any(l.startswith("[dry run] autobleem-pc-tools: tag v2.0.0-alpha2 ") for l in self.lines))

    def test_check_existing_build_skips_waiting_for_an_already_successful_build(self):
        gh = TagPrecheckGitHub(self.branches, [], self.lines.append,
                               runs_by_repo_tag={("autobleem", "v2.0.0-alpha2"):
                                                 [{"status": "completed", "conclusion": "success"}]})
        self.assertTrue(release.check_existing_build(gh, "autobleem", "v2.0.0-alpha2", log=self.lines.append))

    def test_check_existing_build_waits_again_for_a_failed_or_missing_build(self):
        gh = TagPrecheckGitHub(self.branches, [], self.lines.append,
                               runs_by_repo_tag={("autobleem", "v2.0.0-alpha2"):
                                                 [{"status": "completed", "conclusion": "failure"}]})
        self.assertFalse(release.check_existing_build(gh, "autobleem", "v2.0.0-alpha2", log=self.lines.append))
        self.assertFalse(release.check_existing_build(gh, "autobleem", "v2.0.0-alpha3", log=self.lines.append))


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

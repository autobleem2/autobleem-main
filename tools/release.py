#!/usr/bin/env python3
"""release.py - the nightly refresh and the promotions of the AutoBleem 2 components, over the GitHub API.

  release.py nightly [--platforms "rpi-armhf psc ..."] [--all] [--dry-run]
      each component whose develop moved past its rolling `nightly` release is rebuilt on develop (--all:
      every one), those builds are awaited, then autobleem-appliance assembles the nightly for the platforms -
      a no-op when the site's nightly was built from these same components already (each component's nightly
      starts that assembly itself since 2026-09-26); --all always assembles
  release.py promote {alpha|beta|rc|release} [--version X.Y.Z] [--dry-run]
      alpha/beta: the next vX.Y.Z-alphaN / -betaN tag on develop's head of every component
      rc:         release/vX.Y.Z cut from develop in every component (first rc), vX.Y.Z-rcN tagged on it
      release:    vX.Y.Z tagged on the release branches, merged into master and back into develop
      Before the first tag: autobleem-build's master is moved to develop's head when it is behind (every v*
      tag - alpha/beta/rc/release alike - compiles against its :latest), and that move's image.yml build is
      awaited when it actually touches what the image rebuilds for (R2). Components are then tagged in
      dependency order and each stage's tag builds are awaited before the next; the appliance's tag comes
      last - its build assembles the components' releases and publishes the channel.
      Refuses to start (even with --dry-run) unless proc_unzip, ext_store and autobleem-themes already have a
      released v* version of their own - they keep their own versioning and are never tagged by this script.
  release.py next {alpha|beta|rc|release} [--version X.Y.Z]
      only prints the tag a promotion would make (what the admin panel shows before its confirmation)

Needs GH_TOKEN: a token that can push tags and branches and dispatch workflows in every repository - the
autobleem-admin GitHub App's installation token in CI (the default GITHUB_TOKEN reaches only its own
repository). Standard library only. docs/admin-panel-plan.md has the why.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ORG = "autobleem2"
API = "https://api.github.com"

# the components of a release, in stages: a stage's tag builds must succeed before the next stage is tagged
# (console-tools' tag build takes the kernel payload released under the same tag). autobleem-core has no
# release of its own; it is tagged with the rest so every version names the core it was built with.
STAGES = [
    ["psc-kernel-payload", "autobleem-core"],
    ["pcsx-abnxt", "autobleem", "autobleem-pc-tools"],
    ["autobleem-console-tools"],
]
APPLIANCE = "autobleem-appliance"
# pcsx-ab is frozen at its own v1.0-final (the owner, 2026-09-27; docs/decisions.md): never tagged with the
# unified vX.Y.Z and never a nightly source - every package takes that one release
# (autobleem-appliance tools/release_assets.sh, PCSXAB_FROZEN_TAG), so it is in neither STAGES nor
# NIGHTLY_REPOS.
# the build image: every v* tag (alpha/beta/rc/release alike, docs/decisions.md "two channels") compiles in
# its master's :latest, never its develop's :develop - so promote() moves master to develop's head, and waits
# for image.yml's push build to publish the new :latest, before the first STAGES tag is created. Not a
# component of the release itself (it gets no vX.Y.Z tag), so it is not in STAGES or repos().
BUILD_IMAGE = "autobleem-build"
# image.yml's own paths-filter (its `on: push: paths:`) - a merge that touches neither means no rebuild ever
# starts, so promote() must not wait for one
BUILD_IMAGE_WATCHED_PATHS = ("docker/**", ".github/workflows/image.yml")
# proc_unzip, ext_store and autobleem-themes keep versions of their own (docs/decisions.md,
# 2026-09-26): a promotion never tags them with the unified vX.Y.Z, so they are deliberately not in
# STAGES. promote() only checks each already has a released (non-prerelease) v* version of its own - tagged
# by hand in its own repository, not by this script - so the appliance's release build has something other
# than a nightly to bundle (autobleem-appliance's release_assets.sh errors otherwise). proc_unzip and
# ext_store were tagged for the first time on 2026-09-26 (v1.1.0, v1.0.1); autobleem-themes joined here D5,
# 2026-09-27 (its package build, staged by the appliance's stage_themes) - it has no v* tag yet.
OWN_VERSION_REPOS = ["proc_unzip", "ext_store", "autobleem-themes"]
# the workflow that builds a component - its develop into the rolling `nightly` release, a tag into that
# tag's release. A tag push may start other workflows too (the launcher's test gate); this is the one
# awaited. autobleem-core has none (no release of its own).
WORKFLOWS = {
    "psc-kernel-payload": "build.yml",
    "pcsx-ab": "build.yml",
    "pcsx-abnxt": "build.yml",
    "autobleem": "publish-launcher.yml",
    "autobleem-console-tools": "build.yml",
    "autobleem-pc-tools": "build.yml",
    "ext_store": "build.yml",
    "proc_unzip": "build.yml",
    "autobleem-themes": "build.yml",
    "autobleem-appliance": "assemble.yml",
    "autobleem-build": "image.yml",
}
# the components whose develop feeds the nightly (the kernel payload reaches it through its releases) - the
# same list as the appliance's fingerprint (assemble.yml's plan; autobleem-themes joined it D5, 2026-09-27)
NIGHTLY_REPOS = ["pcsx-abnxt", "autobleem", "autobleem-console-tools", "autobleem-pc-tools",
                 "ext_store", "proc_unzip", "autobleem-themes"]
# what a component's develop build does not run for (its workflow's paths-ignore): a commit touching only these
# publishes no nightly, so develop's head stays past the `nightly` tag - and is no reason to rebuild
IGNORED_PATHS = {"autobleem": ("docs/**", "**.md", "manuals/**")}
# the components whose workflow can build a feature branch as the rolling `preview` release (its `channel`
# input, PLATFORM-20); proc_unzip has no such input yet, so a preview always takes its nightly
PREVIEW_REPOS = [r for r in NIGHTLY_REPOS if r != "proc_unzip"]
# a branch name a preview takes: what git allows that is also safe in a site folder name
PREVIEW_BRANCH = re.compile(r"^(?!.*\.\.)[A-Za-z0-9][A-Za-z0-9._/-]{0,99}\Z")
ALL_PLATFORMS = "rpi-armhf rpi-arm64 pcusb psc win"
KINDS = ("alpha", "beta", "rc", "release")
# -alpha3 is the scheme (docs/versioning.md); -alpha.3 is read too, should one ever be made by hand
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc|pre)\.?(\d+))?$")


# ------------------------------------------------------------------------------------------------ versions
def parse_tag(tag):
    """'v2.0.0-alpha3' -> ((2, 0, 0), 'alpha', 3); 'v2.0.0' -> ((2, 0, 0), None, 0); anything else -> None"""
    m = TAG_RE.match(tag)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))), m.group(4), int(m.group(5) or 0)


def next_tag(tags, kind, version=None):
    """The tag a promotion of `kind` makes, given the launcher's existing tags.

    The base X.Y.Z is `version` when given, else the newest pre-release's base (the release being prepared)
    - a stable tag's base is done, so without a pre-release after it a version must be given.

    How it counts (R1 step 4 - this was read wrong once, proposing v2.0.0-alpha3 while alpha2 was still the
    live testing tag): for a base already in `tags`, the next number for `kind` is one past the highest
    existing `-<kind><N>` tag of that base *in the "autobleem" repository's own tag list* - the only list
    this function is ever called with (see promote() and `next`'s cmd). It does not know or care whether an
    alpha2/alpha3 tag was ever withdrawn from the download site or deleted from GitHub; it only reads tags
    that still exist. So: while v2.0.0-alpha1 and v2.0.0-alpha2 both exist on "autobleem", the next alpha is
    v2.0.0-alpha3 - correct today, and exactly why R1's plan deletes the old alpha2 (and psc-kernel-payload's
    alpha3) tags before the new-alpha2 promote runs. Once v2.0.0-alpha2 is deleted from every repository in
    the train (R1 steps 7-10, not this script's job), leaving only v2.0.0-alpha1 on "autobleem", this same
    logic yields v2.0.0-alpha2 again on its own - no change needed here for that half of R1."""
    parsed = [(t, p) for t, p in ((t, parse_tag(t)) for t in tags) if p]
    if version:
        m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", version)
        if not m:
            raise ValueError("version must be X.Y.Z, not %r" % version)
        base = tuple(int(x) for x in m.groups())
    else:
        released = {p[0] for _, p in parsed if p[1] is None}
        open_bases = sorted({p[0] for _, p in parsed if p[1] is not None and p[0] not in released})
        if not open_bases:
            raise ValueError("no pre-release in progress - give --version X.Y.Z for the next one")
        base = open_bases[-1]
    if base in {p[0] for _, p in parsed if p[1] is None}:
        raise ValueError("v%d.%d.%d is released already" % base)
    name = "v%d.%d.%d" % base
    if kind == "release":
        return name
    n = max([p[2] for _, p in parsed if p[0] == base and p[1] == kind] or [0]) + 1
    return "%s-%s%d" % (name, kind, n)


def glob_regex(pattern):
    """a paths-ignore glob as GitHub reads it: ** any characters, * and ? none of them a /"""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def path_ignored(path, patterns):
    return any(glob_regex(p).match(path) for p in patterns)


def release_branch(tag):
    return "release/" + re.sub(r"-.*$", "", tag)


# ---------------------------------------------------------------------------------------------- the API
class GitHub:
    def __init__(self, token, dry_run=False, log=print):
        self.token, self.dry_run, self.log = token, dry_run, log

    def call(self, method, path, body=None, ok404=False):
        req = urllib.request.Request(API + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode()
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as e:
            if ok404 and e.code == 404:
                return None
            raise RuntimeError("%s %s: HTTP %d %s" % (method, path, e.code, e.read().decode()[:300]))

    def write(self, method, path, body, what):
        """a change - only printed on a dry run"""
        self.log(("[dry run] " if self.dry_run else "") + what)
        return None if self.dry_run else self.call(method, path, body)

    # reads
    def tags(self, repo):
        out, page = [], 1
        while True:
            chunk = self.call("GET", "/repos/%s/%s/tags?per_page=100&page=%d" % (ORG, repo, page))
            out += [t["name"] for t in chunk]
            if len(chunk) < 100:
                return out
            page += 1

    def branch_sha(self, repo, branch):
        b = self.call("GET", "/repos/%s/%s/branches/%s" % (ORG, repo, branch), ok404=True)
        return b["commit"]["sha"] if b else None

    def tag_commit(self, repo, tag):
        ref = self.call("GET", "/repos/%s/%s/git/ref/tags/%s" % (ORG, repo, tag), ok404=True)
        if not ref:
            return None
        obj = ref["object"]
        while obj["type"] == "tag":  # an annotated tag points at its tag object first
            obj = self.call("GET", "/repos/%s/%s/git/tags/%s" % (ORG, repo, obj["sha"]))["object"]
        return obj["sha"]

    def latest_release_tag(self, repo):
        """the repository's latest release's tag - GitHub's own idea of "latest": the most recent release
        that is neither a draft nor a prerelease. None when there is no such release (a 404, or every
        release so far is a prerelease)."""
        rel = self.call("GET", "/repos/%s/%s/releases/latest" % (ORG, repo), ok404=True)
        return rel["tag_name"] if rel else None

    def compare(self, repo, base, head):
        """GitHub's comparison of two commits: status (ahead, behind, diverged, identical) and the files"""
        return self.call("GET", "/repos/%s/%s/compare/%s...%s" % (ORG, repo, base, head))

    def runs(self, repo, query):
        """the runs of the repository's release workflow (WORKFLOWS) the query selects, newest first"""
        return self.call("GET", "/repos/%s/%s/actions/workflows/%s/runs?per_page=30&%s"
                         % (ORG, repo, WORKFLOWS[repo], query))["workflow_runs"]

    # writes
    def create_tag(self, repo, tag, sha, message):
        if self.dry_run:
            return self.write(None, None, None, "%s: tag %s on %s" % (repo, tag, sha[:7]))
        obj = self.call("POST", "/repos/%s/%s/git/tags" % (ORG, repo),
                        {"tag": tag, "message": message, "object": sha, "type": "commit"})
        return self.write("POST", "/repos/%s/%s/git/refs" % (ORG, repo),
                          {"ref": "refs/tags/" + tag, "sha": obj["sha"]}, "%s: tag %s on %s" % (repo, tag, sha[:7]))

    def create_branch(self, repo, branch, sha):
        return self.write("POST", "/repos/%s/%s/git/refs" % (ORG, repo), {"ref": "refs/heads/" + branch, "sha": sha},
                          "%s: branch %s from %s" % (repo, branch, sha[:7]))

    def merge(self, repo, base, head, message):
        return self.write("POST", "/repos/%s/%s/merges" % (ORG, repo),
                          {"base": base, "head": head, "commit_message": message},
                          "%s: merge %s into %s" % (repo, head, base))

    def dispatch(self, repo, workflow, ref, inputs=None):
        return self.write("POST", "/repos/%s/%s/actions/workflows/%s/dispatches" % (ORG, repo, workflow),
                          {"ref": ref, "inputs": inputs or {}},
                          "%s: run %s on %s %s" % (repo, workflow, ref, json.dumps(inputs or {})))


# ---------------------------------------------------------------------------------------------- waiting
def wait_for_runs(gh, wanted, timeout=5 * 3600, poll=30, log=print, superseded=None):
    """wanted: {repo: (query, since)} - the newest run each query finds created at or after `since` (UTC ISO),
    followed until it completes. Fails when one does not succeed or none turns up in 10 minutes.
    superseded: {repo: query} - a run of that repository cancelled with a newer run of the query created after
    it was replaced in its concurrency group (the appliance's assemble keeps one pending run, the newest), and
    the newer one is followed instead."""
    if gh.dry_run:
        for repo in wanted:
            log("[dry run] %s: would wait for its run" % repo)
        return
    wanted, superseded = dict(wanted), superseded or {}
    start, found, done = time.time(), {}, {}
    while len(done) < len(wanted):
        for repo, (query, since) in wanted.items():
            if repo in done:
                continue
            runs = [r for r in gh.runs(repo, query) if r["created_at"] >= since]
            if not runs:
                if time.time() - start > 600:
                    raise RuntimeError("%s: no run started for %s" % (repo, query))
                continue
            run = max(runs, key=lambda r: r["created_at"])
            if found.get(repo) != run["id"]:
                found[repo] = run["id"]
                log("%s: %s %s" % (repo, run["name"], run["html_url"]))
            if run["status"] == "completed" and run["conclusion"] == "cancelled" and repo in superseded:
                newer = [r for r in gh.runs(repo, superseded[repo]) if r["created_at"] > run["created_at"]]
                if newer:
                    log("%s: %s was replaced by a newer run - following that" % (repo, run["html_url"]))
                    wanted[repo] = (superseded[repo], min(r["created_at"] for r in newer))
                    continue
            if run["status"] == "completed":
                done[repo] = run["conclusion"]
                log("%s: %s" % (repo, run["conclusion"]))
                if run["conclusion"] != "success":
                    raise RuntimeError("%s: %s - %s" % (repo, run["conclusion"], run["html_url"]))
        if len(done) < len(wanted):
            if time.time() - start > timeout:
                raise RuntimeError("timed out waiting for " + ", ".join(set(wanted) - set(done)))
            time.sleep(poll)


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------------------------- nightly
def only_ignored_changes(gh, repo, built, head):
    """develop moved past the nightly with commits its build does not run for (IGNORED_PATHS) only"""
    patterns = IGNORED_PATHS.get(repo)
    if not patterns or not built or not head:
        return False
    c = gh.compare(repo, built, head)
    files = [f["filename"] for f in (c.get("files") or [])]
    # the API lists at most 300 files: a longer list is taken for a real change
    return c.get("status") == "ahead" and 0 < len(files) < 300 and all(path_ignored(f, patterns) for f in files)


def nightly(gh, platforms, rebuild_all=False, log=print):
    stale = []
    for repo in NIGHTLY_REPOS:
        head, built = gh.branch_sha(repo, "develop"), gh.tag_commit(repo, "nightly")
        if not rebuild_all and head and head == built:
            log("%s: nightly is develop's head %s" % (repo, head[:7]))
        elif not rebuild_all and only_ignored_changes(gh, repo, built, head):
            log("%s: develop %s is past nightly %s by documentation only - up to date"
                % (repo, head[:7], built[:7]))
        else:
            stale.append(repo)
            log("%s: develop %s, nightly %s - rebuilding" % (repo, (head or "?")[:7], (built or "none")[:7]))
    since = utc_now()
    for repo in stale:
        gh.dispatch(repo, WORKFLOWS[repo], "develop")
    wait_for_runs(gh, {r: ("event=workflow_dispatch&branch=develop", since) for r in stale}, log=log)
    # each rebuilt component's nightly has started an assembly of its own (repository_dispatch); this one queues
    # behind it and does nothing when that one already published these components (skip_unchanged). --all asks
    # for an assembly whatever the site has.
    since = utc_now()
    gh.dispatch(APPLIANCE, WORKFLOWS[APPLIANCE], "develop",
                {"channel": "nightly", "platforms": platforms, "skip_unchanged": "false" if rebuild_all else "true"})
    wait_for_runs(gh, {APPLIANCE: ("event=workflow_dispatch&branch=develop", since)}, log=log,
                  superseded={APPLIANCE: "branch=develop"})
    log("nightly refreshed for: " + platforms)


# ---------------------------------------------------------------------------------------------- preview
def preview(gh, branch, platforms, log=print):
    """A preview build of a feature branch (PLATFORM-20): every component that has the branch builds it into
    its rolling `preview` release, then the appliance assembles them with every other component's nightly and
    publishes preview/<version>/ on the site. Never touches a `nightly` release or the nightly folder."""
    if not PREVIEW_BRANCH.match(branch or "") or branch in ("develop", "master", "main"):
        raise ValueError("not a feature branch: %r" % branch)
    built = [r for r in PREVIEW_REPOS if gh.branch_sha(r, branch)]
    if not built:
        raise ValueError("no component has a branch %s" % branch)
    for repo in PREVIEW_REPOS:
        log("%s: %s" % (repo, "builds %s" % branch if repo in built else "takes its nightly"))
    since = utc_now()
    for repo in built:
        gh.dispatch(repo, WORKFLOWS[repo], branch, {"channel": "preview"})
    wait_for_runs(gh, {r: ("event=workflow_dispatch&branch=" + branch, since) for r in built}, log=log)
    # the assembly runs from the appliance's develop (its workflow), with its own concurrency group: a nightly
    # arriving meanwhile never replaces it
    since = utc_now()
    gh.dispatch(APPLIANCE, WORKFLOWS[APPLIANCE], "develop",
                {"channel": "preview", "platforms": platforms, "preview_repos": " ".join(built), "branch": branch})
    wait_for_runs(gh, {APPLIANCE: ("event=workflow_dispatch&branch=develop", since)}, log=log)
    log("preview of %s published for: %s" % (branch, platforms))


# ---------------------------------------------------------------------------------------------- promote
def check_own_version_repos(gh, log=print):
    """OWN_VERSION_REPOS never get the unified tag - they must already have a released v* version of their
    own, or a release build has nothing but a nightly to bundle (autobleem-appliance's release_assets.sh
    now refuses that). Read-only, so it runs in a dry run too, before promote() creates or tags anything."""
    for repo in OWN_VERSION_REPOS:
        tag = gh.latest_release_tag(repo)
        if not tag or not tag.startswith("v"):
            raise RuntimeError("%s: no released v* version yet - it keeps its own version (docs/decisions.md) "
                               "and is not tagged by this script; tag a v* release in %s by hand first"
                               % (repo, repo))
        log("%s: keeps its own version, latest release %s" % (repo, tag))


EPOCH = "1970-01-01T00:00:00Z"


def precheck_tags(gh, tag, source, repos, log=print):
    """R1 step 4: refuse to promote if `tag` already exists in any repository of the train on a commit other
    than the one this promotion is about to tag - a leftover from an earlier, withdrawn promotion (the old
    v2.0.0-alpha2/alpha3 tags, R1) must be deleted by hand first, never silently re-pointed or collided with
    (create_tag has no existence check of its own, so without this a stale tag would fail the API call
    mid-promote - after some repos were already tagged). Read-only (every call is a GET), so it runs the
    same way on a dry run: `promote --dry-run` shows exactly which repos would be reused and which created,
    and still stops before anything is created if a real conflict exists.

    Returns {repo: bool} - True where `tag` already sits on the intended commit in that repository (reuse
    it, do not recreate it), False where it does not exist yet (create it)."""
    reuse = {}
    for repo in repos:
        existing = gh.tag_commit(repo, tag)
        if existing is None:
            log("%s: %s does not exist yet - will create it on %s" % (repo, tag, source[repo][:7]))
            reuse[repo] = False
            continue
        if existing != source[repo]:
            raise RuntimeError(
                "%s: tag %s already exists on %s, not on %s - this promotion cannot re-issue it; delete the "
                "stale tag (and its release, if any) in %s first, then promote again"
                % (repo, tag, existing[:7], source[repo][:7], repo))
        log("%s: %s already exists on %s - reusing it, not recreating" % (repo, tag, existing[:7]))
        reuse[repo] = True
    return reuse


def check_existing_build(gh, repo, tag, log=print):
    """True if `repo`'s build of `tag` already completed successfully - a reused tag (precheck_tags) from an
    earlier, interrupted promote run may already have one, and promote() should not wait for a second."""
    if repo not in WORKFLOWS:
        return True
    for run in gh.runs(repo, "event=push&branch=" + tag):
        if run["status"] == "completed":
            done = run["conclusion"] == "success"
            log("%s: %s's existing build for %s %s" % (repo, tag, tag, "succeeded" if done else "did not succeed"))
            return done
    return False


def resume_tag(gh, kind, version=None, log=print):
    """The tag of an interrupted promotion of `kind`, or None. next_tag counts from the launcher's tags, and the
    launcher is tagged in the first stage - so after a promote that stopped half-way (2026-10-03: alpha1 failed at
    console-tools' sdk-abi) it proposed the next number (alpha2) instead of finishing alpha1. A promotion is
    finished when the appliance (the last stage) has the tag and its build succeeded; the launcher's newest tag
    of `kind` without that is the one to finish. (A plain release tag is not resumed this way: next_tag refuses a
    released version.)"""
    if kind == "release":
        return None
    nxt = next_tag(gh.tags("autobleem"), kind, version)
    m = re.match(r"^(.*-%s)(\d+)$" % kind, nxt)
    if not m or int(m.group(2)) < 2:
        return None
    prev = "%s%d" % (m.group(1), int(m.group(2)) - 1)
    if not gh.tag_commit("autobleem", prev):
        return None
    if gh.tag_commit(APPLIANCE, prev) and check_existing_build(gh, APPLIANCE, prev, log=log):
        return None
    log("%s was not finished (the appliance has no successful build of it) - finishing it, not starting %s"
        % (prev, nxt))
    return prev


def rerun_failed_build(gh, repo, tag, log=print):
    """A reused tag's build that failed is run again (its failed jobs), and followed once it is queued - an
    interrupted promote stopped on exactly such a build (2026-10-03: console-tools' sdk-abi)."""
    runs = gh.runs(repo, "event=push&branch=" + tag)
    if not runs or runs[0]["status"] != "completed" or runs[0]["conclusion"] == "success":
        return
    run = runs[0]
    gh.write("POST", "/repos/%s/%s/actions/runs/%d/rerun-failed-jobs" % (ORG, repo, run["id"]), {},
             "%s: run the failed jobs of %s again" % (repo, run["html_url"]))
    if gh.dry_run:
        return
    for _ in range(30):  # until GitHub shows it queued again, so the wait below follows the new attempt
        time.sleep(2)
        if gh.call("GET", "/repos/%s/%s/actions/runs/%d" % (ORG, repo, run["id"]))["status"] != "completed":
            return


def image_rebuild_needed(files):
    """whether autobleem-build's image.yml would run a build for a diff touching `files` - its own
    `on: push: paths:` filter (docker/**, its own workflow file). A diff of 300+ files (the API's page limit,
    so the real list is unknown) is taken as yes - safer to wait for a build that turns out unneeded than to
    skip one that was."""
    return len(files) >= 300 or any(path_ignored(f, BUILD_IMAGE_WATCHED_PATHS) for f in files)


def sync_build_image_master(gh, log=print):
    """R2: autobleem-build's master is what every v* tag compiles in (:latest) - a tag created while master
    is still behind develop would build its component against a stale toolchain image, exactly the drift
    this step exists to close. Called once, before promote() creates the first STAGES tag (any kind: alpha/
    beta/rc/release are all v* tags, docs/decisions.md's "two channels").

    Whether master needs moving is an ahead/behind **compare**, never a plain sha equality check: a merge
    of develop into master gives master a brand new sha even though it now contains every commit develop
    has, so "master's sha != develop's sha" alone would call an already-caught-up master "still behind" and
    try to merge it again on every single promotion from then on (found the hard way against the real repo
    while building this - master's own catch-up merge commit differs from develop's head, and GitHub's
    compare correctly answers "behind" for that pair, not "identical"). `compare(master, develop).status`
    of `identical` or `behind` means master already has develop's head; `ahead` or `diverged` means it does
    not.

    A no-op - reads only, no merge, no wait - when master already has develop's head; that includes a dry
    run of an already-caught-up train, so `promote --dry-run` still moves nothing when there is nothing to
    move. Otherwise it merges develop into master (GitHub.merge - skipped under dry_run, GitHub.write's own
    rule) and, only when that diff actually touches what image.yml's paths-filter watches
    (image_rebuild_needed - a merge of unrelated files never starts a build, so waiting for one would just
    time out), waits for the resulting push build to publish the new :latest before returning."""
    develop_sha = gh.branch_sha(BUILD_IMAGE, "develop")
    if not develop_sha:
        raise RuntimeError("%s: no develop branch" % BUILD_IMAGE)
    master_sha = gh.branch_sha(BUILD_IMAGE, "master")
    if master_sha == develop_sha:
        log("%s: master already matches develop %s - nothing to move" % (BUILD_IMAGE, develop_sha[:7]))
        return
    c = gh.compare(BUILD_IMAGE, master_sha, develop_sha) if master_sha else {"status": "ahead", "files": []}
    if c.get("status") in ("identical", "behind"):
        log("%s: master %s already has develop %s (compare: %s) - nothing to move"
            % (BUILD_IMAGE, master_sha[:7], develop_sha[:7], c.get("status")))
        return
    files = [f["filename"] for f in (c.get("files") or [])]
    rebuild = image_rebuild_needed(files)
    log("%s: master %s is behind develop %s (compare: %s) - moving it before any v* tag compiles%s"
        % (BUILD_IMAGE, (master_sha or "none")[:7], develop_sha[:7], c.get("status"),
           "" if rebuild else " (no docker/image.yml change in the diff - no rebuild expected)"))
    since = utc_now()
    gh.merge(BUILD_IMAGE, "master", "develop", "Move autobleem-build's master to develop for a promotion")
    if rebuild:
        wait_for_runs(gh, {BUILD_IMAGE: ("event=push&branch=master", since)}, log=log)
    else:
        log("%s: master moved, no image rebuild to wait for" % BUILD_IMAGE)


def promote(gh, kind, version=None, log=print):
    check_own_version_repos(gh, log=log)
    resumed = resume_tag(gh, kind, version, log=log)
    tag = resumed or next_tag(gh.tags("autobleem"), kind, version)
    branch = release_branch(tag)
    log("promotion: %s -> %s%s" % (kind, tag, " (resumed)" if resumed else ""))
    repos = [r for stage in STAGES for r in stage] + [APPLIANCE]
    # where each repository's tag goes: develop for alpha/beta, the release branch for rc and release - and
    # when finishing an interrupted promotion, where it already went (develop may have moved on since)
    source = {}
    for repo in repos:
        existing = gh.tag_commit(repo, tag) if resumed else None
        if existing:
            source[repo] = existing
        elif kind in ("alpha", "beta"):
            source[repo] = gh.branch_sha(repo, "develop")
        else:
            sha = gh.branch_sha(repo, branch)
            if not sha:
                sha = gh.branch_sha(repo, "develop")
                gh.create_branch(repo, branch, sha)
            source[repo] = sha
        if not source[repo]:
            raise RuntimeError("%s: no commit to tag" % repo)
    # pre-check every repo's target tag before creating anything (R1 step 4) - see precheck_tags()
    reuse = precheck_tags(gh, tag, source, repos, log=log)
    # R2: move autobleem-build's master (and let :latest rebuild) before the first STAGES tag below - every
    # v* tag compiles against it
    sync_build_image_master(gh, log=log)
    for stage in STAGES + [[APPLIANCE]]:
        since = utc_now()
        for repo in stage:
            if not reuse[repo]:
                gh.create_tag(repo, tag, source[repo], "AutoBleem %s" % tag)
        waiting = {}
        for repo in stage:
            if repo == "autobleem-core":
                continue
            if reuse[repo]:
                if check_existing_build(gh, repo, tag, log=log):
                    continue
                rerun_failed_build(gh, repo, tag, log=log)
                waiting[repo] = ("event=push&branch=" + tag, EPOCH)  # an older, not-yet-finished run
            else:
                waiting[repo] = ("event=push&branch=" + tag, since)
        wait_for_runs(gh, waiting, log=log)
    if kind == "release":
        for repo in repos:
            gh.merge(repo, "master", branch, "Release %s" % tag)
            gh.merge(repo, "develop", branch, "Merge %s back into develop" % branch)
    log("done: %s is on the %s channel" % (tag, "release" if kind == "release" else "testing"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nightly")
    n.add_argument("--platforms", default=ALL_PLATFORMS)
    n.add_argument("--all", action="store_true")
    n.add_argument("--dry-run", action="store_true")
    pv = sub.add_parser("preview")
    pv.add_argument("--branch", required=True)
    pv.add_argument("--platforms", default=ALL_PLATFORMS)
    pv.add_argument("--dry-run", action="store_true")
    for name in ("promote", "next"):
        p = sub.add_parser(name)
        p.add_argument("kind", choices=KINDS)
        p.add_argument("--version")
        if name == "promote":
            p.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set")
    gh = GitHub(token, dry_run=getattr(args, "dry_run", False))
    try:
        if args.cmd == "next":
            print(resume_tag(gh, args.kind, args.version, log=lambda m: None) or next_tag(gh.tags("autobleem"), args.kind, args.version))
        elif args.cmd == "nightly":
            nightly(gh, " ".join(args.platforms.split()), args.all)
        elif args.cmd == "preview":
            preview(gh, args.branch, " ".join(args.platforms.split()))
        else:
            promote(gh, args.kind, args.version)
    except (RuntimeError, ValueError) as e:
        sys.exit("release.py: %s" % e)


if __name__ == "__main__":
    main()

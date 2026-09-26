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
      Components are tagged in dependency order and each stage's tag builds are awaited before the next; the
      appliance's tag comes last - its build assembles the components' releases and publishes the channel.
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
    ["pcsx-ab", "pcsx-abnxt", "autobleem", "autobleem-pc-tools"],
    ["autobleem-console-tools"],
]
APPLIANCE = "autobleem-appliance"
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
    "autobleem-appliance": "assemble.yml",
}
# the components whose develop feeds the nightly (the kernel payload reaches it through its releases) - the
# same list as the appliance's fingerprint (assemble.yml's plan)
NIGHTLY_REPOS = ["pcsx-ab", "pcsx-abnxt", "autobleem", "autobleem-console-tools", "autobleem-pc-tools",
                 "ext_store", "proc_unzip"]
# what a component's develop build does not run for (its workflow's paths-ignore): a commit touching only these
# publishes no nightly, so develop's head stays past the `nightly` tag - and is no reason to rebuild
IGNORED_PATHS = {"autobleem": ("docs/**", "**.md", "manuals/**")}
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
    - a stable tag's base is done, so without a pre-release after it a version must be given."""
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


# ---------------------------------------------------------------------------------------------- promote
def promote(gh, kind, version=None, log=print):
    tag = next_tag(gh.tags("autobleem"), kind, version)
    branch = release_branch(tag)
    log("promotion: %s -> %s" % (kind, tag))
    repos = [r for stage in STAGES for r in stage] + [APPLIANCE]
    # where each repository's tag goes: develop for alpha/beta, the release branch for rc and release
    source = {}
    for repo in repos:
        if kind in ("alpha", "beta"):
            source[repo] = gh.branch_sha(repo, "develop")
        else:
            sha = gh.branch_sha(repo, branch)
            if not sha:
                sha = gh.branch_sha(repo, "develop")
                gh.create_branch(repo, branch, sha)
            source[repo] = sha
        if not source[repo]:
            raise RuntimeError("%s: no commit to tag" % repo)
    for stage in STAGES + [[APPLIANCE]]:
        since = utc_now()
        for repo in stage:
            gh.create_tag(repo, tag, source[repo], "AutoBleem %s" % tag)
        waiting = {r: ("event=push&branch=" + tag, since) for r in stage if r != "autobleem-core"}
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
            print(next_tag(gh.tags("autobleem"), args.kind, args.version))
        elif args.cmd == "nightly":
            nightly(gh, " ".join(args.platforms.split()), args.all)
        else:
            promote(gh, args.kind, args.version)
    except (RuntimeError, ValueError) as e:
        sys.exit("release.py: %s" % e)


if __name__ == "__main__":
    main()

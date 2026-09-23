#!/usr/bin/env bash
# workspace.sh - every AutoBleem 2 repository, cloned or brought up to date next to this one.
#
#   tools/workspace.sh              clone what is missing (with submodules), fast-forward the rest
#   tools/workspace.sh status       each repository's branch, how far it is from origin, local changes
#   tools/workspace.sh --https      clone over https instead of ssh
#
# The repositories land in this checkout, one folder each (repos.txt; .gitignore keeps them out of this
# repository), so a session started anywhere in the tree reads this CLAUDE.md as well as the repository's
# own. A repository is cloned at develop (the default everywhere). An existing one is only fast-forwarded,
# and only when it is on develop with no local changes - never switched, rebased or reset: other sessions
# may be working in it.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
ORG=autobleem2
URL="git@github.com:$ORG"
MODE=sync
for arg in "$@"; do
    case "$arg" in
        status) MODE=status ;;
        --https) URL="https://github.com/$ORG" ;;
        *) echo "usage: tools/workspace.sh [status] [--https]" >&2; exit 2 ;;
    esac
done

repos() { grep -v '^#' repos.txt | awk 'NF { print $1 }'; }

for name in $(repos); do
    dir="$ROOT/$name"
    if [ "$MODE" = status ]; then
        if [ ! -d "$dir/.git" ]; then printf '%-24s (not cloned)\n' "$name"; continue; fi
        git -C "$dir" fetch -q origin 2>/dev/null || true
        branch=$(git -C "$dir" branch --show-current)
        counts=$(git -C "$dir" rev-list --left-right --count "origin/$branch...HEAD" 2>/dev/null || echo "? ?")
        dirty=$(git -C "$dir" status --porcelain | grep -c . || true)
        printf '%-24s %-22s behind %s ahead %s  %s changed\n' "$name" "$branch" ${counts% *} ${counts#* } "$dirty"
        continue
    fi
    if [ ! -d "$dir/.git" ]; then
        echo "==> clone $name"
        git clone -q --recurse-submodules --branch develop "$URL/$name.git" "$dir"
        continue
    fi
    branch=$(git -C "$dir" branch --show-current)
    if [ "$branch" != develop ] || [ -n "$(git -C "$dir" status --porcelain --untracked-files=no)" ]; then
        echo "==> $name: on $branch or with local changes - left as it is"
        continue
    fi
    echo "==> update $name"
    git -C "$dir" pull -q --ff-only origin develop || echo "    $name: not a fast-forward - left as it is"
    git -C "$dir" submodule update -q --init --recursive
done

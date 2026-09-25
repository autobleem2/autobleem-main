# The 1.x launcher's history: where it is, and what of it came over

Archived plan (done 2026-09-21). The full text is in git history: `git log -- docs/archive/legacy-1x-analysis.md`
(branch-by-branch proof, the search of the old drives, and how the GitLab storage was read).

## Where the code is now

| copy | what | where |
|---|---|---|
| **`screemerpl/autobleem-1x`** (private) | the old GitLab's `root/autobleem`: 1572 commits, 2018-12 -> 2022-04, 9 branches, tags `v0.1b`..`v0.9.0` | GitHub; clone at `E:\Programming\autobleem-1x`; bare mirror `psc-build:~/gitlab-mirror/root-autobleem.git` |
| **`screemerpl/autobleem-ng`** (private) | AutoBleem-NG's `main` (`b7bc39a2`, 2026-06-01) + tag `v1.1.0`, recovered from the clone the port was made from (the NG org is gone from GitHub) | GitHub; clone at `E:\Programming\autobleem-ng` |
| the GitLab's other projects | `pscbios`, `abflashkit`, `autobleem-payload`, `psc-bluez`, `psc-rootfs`, `libmamecd`, `autobleem-build`, `autobleem-themes-pack`, `autobleem-gameports-pack`, `pcsx-ab-2020`, `amiberry-psc`, `psc-toolchain`, `openbor-psc` - private; `psc-kernel` moved to `autobleem2/psc-kernel` (public, a build input) | GitHub under `screemerpl`; every one also bare in `psc-build:~/gitlab-mirror` |
| the Mac's working trees | `NetBeansProjects/cbleemsync` (HEAD `feature/chd`, uncommitted work of 2021-03-29) and `Programowanie/autobleem` (2020-03) | the imaged Mac SSD on `G:` |

## The lineage

```
2018-12 ... 924a02cb (develop, 2021-03-14) == AutoBleem 2's root commit
                 \
                  feature/lightgun_support (Axanar, 29 commits, 2022-03/04)   <- the GitLab's newest
                           \
                            AutoBleem-NG main: +93 more (Axanar to 2022-08, cornelk 2025-12 -> 2026-06), v1.1.0
```

**Our base is the GitLab's `develop` tip exactly**, and every tag is on it. The only branch ahead with
features, `feature/lightgun_support`, is the start of the NG line, which was ported on 2026-09-18 - lightguns
live in `LightgunService`, `GameSet::Lightgun`, the RA game editor and the meta panel's icons. Not ported, on
purpose: `feature/Eris_merge` (Project Eris is dead; our layout is decided), `feature/refactoring` (a first UI
library, superseded by `lib_ableem`/`ab_classic`) and `ci` (superseded by the Docker image). Everything NG did
after the lightgun merge is in 2.x in one form or another - **no open item from NG**.

## The owner's own post-0.9.1 work

No `screemer` commit exists after `924a02cb` anywhere searched (every local drive, the NAS, the VM disks, the
Mac SSD). The one uncommitted tree, `cbleemsync` of 2021-03-29, added `libs/abtools` - every path as a key in a
`platform_mac.ini` - which 2.x implemented as `PlatformConfig` + `resources/platform/<platform>.ini`. Its
reason (games movable into sub-folders of `Games/` keeping their cards and saves) is done too: save states
have been central since 1.x (`Games/!SaveStates/<folder name>/`, keyed by the folder's *name*), and since
2026-09-21 a rescan recognises a moved folder (`ScanService`'s vanished rows claimed by folder name + disc
names -> `GameDatabase::updateGamePath`), so id, history and last_played survive. A folder that is *renamed*
is a new game. If older work turns up on a machine not searched, look for a `cbleemsync`/`autobleem` folder
with `src/code/launcher/gui_launcher.cpp` newer than 2021-03-14, or a `libs/abtools` folder.

## Lasting gotcha

Two different games whose folders share a name in two sub-folders share one `!SaveStates/<name>/`
(`GameCatalogService::deleteUsbGame` refuses to delete a shared one). Keying by serial would move every
existing stick's states - left alone unless it bites.

## Still open

- Retire the old GitLab on the build server (root): `docker compose down` in `/srv/gitlab`, remove
  `/etc/nginx/sites-enabled/gitlab.conf` and reload nginx, then remove `/srv/gitlab` and the
  `gitlab/gitlab-ce` image. Keep `~/gitlab-mirror` until the GitHub copies have been cloned elsewhere once.
- Optional: graft the 1.x history onto the launcher per clone (`git remote add legacy
  https://github.com/screemerpl/autobleem-1x.git`, `git fetch legacy`, `git replace --graft <our root>
  924a02cb`), so `git blame` reaches 2018.
- Check the game editor on `ab2` (and `aergb`): 18 rows since the Boot logo row in a `menuPanel.h` of 560
  (`default`/`evolution` are taller) - raise it if a row is cut off.
- Game Manager "Move to folder..." (pick or make a sub-folder, rename the game's folder, `updateGamePath`) -
  after the owner's Game Manager rework.

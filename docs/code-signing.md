# Code signing - the Windows programs (2026-09-23)

## Why

A nightly `AutoBleemInstaller.exe` was quarantined by Windows Defender as **`Trojan:Win32/Wacatac.C!ml`**
(2026-09-23, the owner's PC). `!ml` is Defender's machine-learning guess, not a signature: an unsigned,
never-seen exe that is **UPX-packed** looks like a dropper to it. Scanned on the same machine, the packed exe
was detected and the same exe unpacked (`upx -d`) was clean. Two changes follow:

1. **No Windows exe is UPX-packed**, in any script or workflow (`decisions.md`). The console, Pi and PC-stick
   binaries still are - Defender never sees them.
2. **Every Windows program we build is Authenticode-signed** in CI, through **SignPath** - SignPath
   Foundation's free code signing for open-source projects. Signed, the programs build a reputation and
   stop tripping the ML heuristics; the publisher Windows shows is **"SignPath Foundation"** (their
   certificate, not ours).

## What is signed, where

| Repository | Workflow / job | Signed | Unsigned artifact -> signed artifact |
|---|---|---|---|
| autobleem-pc-tools | `build.yml` / `sign` | AutoBleemInstaller.exe, AutoBleemWinSetup.exe, UpdateRoms.exe, AutoBleemFlasher.exe | `pc-tools-win64-unsigned` -> `pc-tools-win64` |
| autobleem (launcher) | `publish-launcher.yml` / `sign-win` | autobleem-gui.exe (the Windows product's) | `launcher-win64-unsigned` -> `launcher-win64` |
| pcsx-ab | `build.yml` / `sign-win` | pcsx-ab.exe | `win-unsigned` -> `dist-win` |
| pcsx-abnxt | `build.yml` / `sign-win` | pcsx-ab.exe | `win-unsigned` -> `dist-win` |
| autobleem-appliance | `assemble.yml` / `sign-win` | AutoBleemSetup-&lt;v&gt;.exe (NSIS; the programs inside arrive signed) | `win-setup-unsigned` -> `payload-win-setup` |

The logic is one composite action, **autobleem-build's `.github/actions/signpath-sign`**: it looks the
unsigned artifact up by name, submits it to SignPath (`signpath/github-action-submit-signing-request@v3`),
waits up to an hour for the request to be approved and signed, and leaves the folder signed at `path`. Each
repository keeps the files it signs in **`.signpath/artifact-configuration.xml`** - a copy of what the
SignPath project's artifact configuration must say (SignPath reads its own, not the file).

- **Signing is switched OFF** (the owner, 2026-09-24) by a per-repository switch, the variable
  **`AB_SIGNING_ENABLED`** - unset, the sign jobs only pass the unsigned files through, quietly. Everything
  below applies to a repository once it is set to `true`. The no-UPX rule does not depend on it.
- **A `v*` tag / release must come back signed**, or the job fails and nothing is released.
- **A develop build / nightly** ships **unsigned** when the request is not approved within the hour (or
  refused), with a warning in the run - a nightly never waits on a person.
- **A pull request is never signed**, and **without the SignPath settings** (below) everything ships unsigned
  exactly as before, with a warning - the wiring is safe to have before the account exists.
- Only our own programs are signed. The SDL2 / MSYS2 runtime DLLs next to them are third-party (the
  Foundation forbids signing them); pcsx-ab's plugin DLLs are left unsigned too, and so is the uninstaller
  NSIS writes at install time.
- SignPath signs only what **GitHub-hosted runners** built: every job leading up to a signing request must be
  hosted. That holds today (the self-hosted jobs - the appliance's images and site publishing, the emulators'
  optional self-hosted Linux build - are not in any signing job's chain); keep it that way.

## What the owner has to do (once)

1. **Apply to SignPath Foundation** (signpath.org, "Apply"). The project qualifies: GPL-3.0-or-later, public
   repositories, released, built in GitHub Actions. They review the application; approval is not instant.
2. **Publish a code signing policy** on the project's home page (the download site and/or the launcher
   README) - the Foundation requires it:
   - "Free code signing provided by SignPath.io, certificate by SignPath Foundation"
   - the team roles - **committers/reviewers** (who may change the code) and **approvers** (who approve each
     signing request); everyone in them uses MFA on GitHub and SignPath
   - a **privacy statement**. Their stock sentence is "This program will not transfer any information to
     other networked systems unless specifically requested by the user or the person installing or operating
     it". Check it against what the programs do before using it: the launcher's update check and online
     cover/rdb downloads (`OnlineAssets`, config.ini `online`), the installer's RetroArch/BIOS fetches, the
     flasher's image download. If any of those runs without being asked, link a short privacy policy instead
     (what is fetched from where, that nothing about the user is sent).
3. **In SignPath**, once approved (then, last, `AB_SIGNING_ENABLED=true` on each of the five repositories): one **project per repository** - slugs `autobleem-pc-tools`, `autobleem`,
   `pcsx-ab`, `pcsx-abnxt`, `autobleem-appliance` (the action defaults to the repository's name; a different
   slug goes in the repository variable `SIGNPATH_PROJECT_SLUG`) - each linked to its GitHub repository as a
   trusted build system, with its `.signpath/artifact-configuration.xml` pasted as the default artifact
   configuration. The signing policy is `release-signing` unless `SIGNPATH_POLICY_SLUG` says otherwise.
4. **In GitHub, on the autobleem2 organisation** (org-level, shared by all five repositories): the variable
   **`SIGNPATH_ORGANIZATION_ID`** and the secret **`SIGNPATH_API_TOKEN`** (a SignPath CI user's API token,
   submitter on the five projects). Nothing else changes; the next build of each repository signs.
5. **Approve requests**: every signing request waits for an approver in SignPath (the Foundation's rule).
   A release is five requests (one per repository); a nightly is one per develop push of a component plus
   the appliance's - approve them to ship signed nightlies, or ignore them and the nightly ships unsigned
   after an hour.

Until then, the quick fix for a flagged download is a false-positive report to Microsoft
(microsoft.com/wdsi/filesubmission) - it clears that file, usually within a day or two.

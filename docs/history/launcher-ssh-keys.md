# `rc/ssh_keys.sh` (C10, 2026-09-26)

What gives SSH into the AutoBleem kernel without the owner hand-editing `boot.sh` on his stick, which the
console's own online update overwrote once already (taking a hand-made block with it).

`System/ssh/authorized_keys` on the stick, if present, is copied into a tmpfs copy of dropbear's root home
(`/home/root` on psc-kernel-payload's overlay - `.ssh` 700, `authorized_keys` 600, both root-owned, which is
what dropbear insists on) and that copy is bind-mounted over `/home/root`. A bind mount is independent of
`/media`, so it outlives the standby loop (the stick is unmounted then; `rc/selection.sh`'s `rndis restart`
after a wake only makes dropbear a fresh host key, not a fresh home) and a stick rewritten from under it by a
reinstall or an online update - nothing here is read from the stick again after boot.

No-op on the stock kernel (`/etc/autobleem` absent - there is no dropbear to feed) and when the stick carries
no key file; idempotent (safe if called again in the same boot). `payload/System/ssh/README.txt` is the
folder's placeholder, in the style of `System/Processors/README.txt`.

See the launcher's own CLAUDE.md, "Runtime layout on the console", for the one-line pointer to this file.

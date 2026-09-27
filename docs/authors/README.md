# Writing for AutoBleem

AutoBleem is a game launcher for the PlayStation Classic (and, from the same code, for the Raspberry Pi, a
PC USB stick and Windows). It can be extended in four ways, each documented on its own page here:

- **[Apps](apps.md)** - third-party programs (games, emulators, tools) that show up in the launcher's Apps
  set and run full-screen, the same way a PS1 game does. Most console homebrew and emulator ports become
  Apps.
- **[Extensions](extensions.md)** - plugins that run inside the launcher itself and can draw their own
  screens with its UI, in the user's theme. Use this when your idea needs to talk to the launcher directly
  (the game library, the Apps list, a background download) rather than just run as its own program.
- **[Scanner processors](processors.md)** - small console programs the launcher's scan runs over the games
  before it reads them: unpacking an archive, converting a format, or otherwise preparing files on disk.
- **[Store catalogs](store-catalog.md)** - a plain text file that tells the AutoBleem Store extension about
  games or Apps it can download. No programming required.

## Platform keys

Apps, extensions and processors all ship one binary per **platform key** - what the target machine was
built for. The launcher tries the most specific key first and falls back to more general ones:

| target machine | keys tried, in order |
|---|---|
| PlayStation Classic | `psc` |
| Raspberry Pi (32-bit) | `rpi`, `linux-armhf` |
| Raspberry Pi (64-bit) | `rpi64`, `linux-arm64` |
| PC USB stick (32-bit) | `pcusb`, `linux-i386` |
| Windows | `win`, `windows-x86_64` |

A binary built for the plain `linux-<arch>` key runs on any Linux machine of that architecture with a
current distribution; the console has no such generic key, because its C library and its SDL2 build are
both older than a stock ARM Linux binary expects, so only a binary built for it will do. Each of the pages
above shows the folder layout a binary goes in.

## Where to ask, and where to report a bug

Every piece of AutoBleem is open source, in its own repository under
[github.com/autobleem2](https://github.com/autobleem2). If you are building against one of the interfaces
described here and something does not work as documented, or you have a question about writing an App,
extension, processor or catalog, open an issue on the relevant repository:

- the launcher itself and the App/extension/processor formats: <https://github.com/autobleem2/autobleem/issues>
- the AutoBleem Store extension and its catalog format: <https://github.com/autobleem2/ext_store/issues>
- the scanner processor template: <https://github.com/autobleem2/proc_template/issues>

When in doubt, the launcher's issue tracker is the right place to start - it gets triaged and forwarded if
another repository turns out to be the better fit.

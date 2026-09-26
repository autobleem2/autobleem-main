# The virtual gamepad for Apps (`apps/abpad/`)

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19). The one standing rule from this section (every App can be left with Reset) stays in CLAUDE.md too.

## The virtual gamepad for Apps (`apps/abpad/`, 2026-09-22)

The third-party Apps on a stick were compiled by other people against other pads, so they take the
console's badly or not at all: the PSC pad's `b0` is Triangle and `b2` is Cross, its d-pad is on two
axes, and it has no hat and no sticks, while nearly every Linux port was written for the wired Xbox
360 pad (`a:b0`, d-pad on hat 0, triggers on axes 2 and 5). RetroBoot papered over this by injecting
a pad configuration into the app's process; this is that, done deliberately and from our own
`gamecontrollerdb.txt`. The design and the reasoning are in `docs/virtual-gamepad-plan.md`.

**`abpadd`** is the one process that reads the pads. It runs SDL2 and reads every pad through the
**GameController API** with our database, so a pad resolves in an App exactly as it resolves in the
launcher and in pcsx - the same code reading the same file - and publishes each player's state in
shared memory (`/tmp/abpad.state`, a seqlock: the reader is inside somebody else's game loop and must
never block or hold a lock). It watches SDL's device events with a slot per player, so player two
unplugging does not shuffle player three into their place, and a pad no database knows is guessed at
and handed to `SDL_GameControllerAddMapping` rather than left invisible - SDL only offers a *mapped*
pad as a GameController. `--probe` says what SDL makes of the pads and through which driver, `--watch`
says what is being published; between them they answer "is it the daemon or the app?" without a
debugger.

**It must run as root.** SDL reaches a modern pad through hidapi, which needs `/dev/hidraw*`, and
those are root-only; without them it falls back to evdev, where the same physical pad has a different
GUID (SDL stamps the driver into it - a trailing `h` is hidapi), a different button layout, and may
match a quite different database line. The launcher runs as root, so anything less makes the daemon
resolve the pad differently from the launcher, which is the one thing it exists not to do. It says so
if it cannot get at hidraw. (This is also the explanation for the Pi 400 pad "re-enumerating" noted
under the Pi port: the same pad seen through two drivers.)

**`libabpad.so`** is preloaded into each App by `rc/app_env.sh` and answers its SDL with a pad it
understands - the wired X360 pad by default, or the PSC's own (`virtual=psc`). It has **no SDL of its
own**: `nm -D -u` finds not one undefined SDL symbol, so it can go in front of an SDL 1.2 app, an SDL2
app or anything else, and every SDL function it calls is found at run time in whatever the app
brought. One library serves both ABIs, which it tells apart by asking the *loaded* library - `dlsym(
RTLD_NEXT, "SDL_SetVideoMode")`, which exists only in SDL 1.2. **Asking the other way round would be
wrong** wherever `libSDL-1.2.so.0` is **sdl12-compat** (SDL 1.2's API on top of SDL2, which is what
Debian ships today): both libraries are then in the process, an SDL2 symbol is found, and an SDL 1.2
app would be answered in SDL2's event structures - unrelated layouts, so corruption rather than a
misread. It covers both the joystick and the `SDL_GameController*` families, ~64 entry points, because
an app using the controller API never calls the joystick ones (SDL2 reaches its own through the dynapi
`_REAL` symbols, which a preload cannot intercept) and would otherwise be the one app with a different
pad. **Every function taking a handle has to be there** or the app hands our pointer to the real SDL;
the two that return a struct by value (`GetBindForButton`/`ForAxis`) are the only ones left out, and
say why.

Other things it does, each because an App needed it: the **d-pad and the left stick feed each other**
(`movement=`, default `both`) - Chocolate Doom is configured with `joystick_x_axis`/`y_axis` and never
looks at a hat, others read only a hat, and no choice of layout fixes that because the layout decides
what the pad *has*, not what the game reads; **no mouse cursor** (`cursor=`), since these machines have
no mouse and it is the app that asks for one; and a **way out** - holding Start+Select escalates
through one gesture, the shim asking the app to quit at ~1.5 s, the daemon (which knows the app's pid)
sending SIGTERM at 3 s and SIGKILL at 5 s. It must be *held*: Start and Select are live buttons in most
games.

**Every App can be left with the console's Reset button** (the owner's rule, 2026-09-25: every game
needs a way out through Reset on the console and from the controller). The Reset button is an input
device's `KEY_PLAYPAUSE` - what SDL 2.0.14 maps to `SDL_SCANCODE_AUDIOPLAY`, the key pcsx-ab
(`plat_sdl.c`, `SACTION_RESET_EVENT`) and pcsx-abnxt (`plat_sdl2.c`, `SACTION_AB_RESET`) leave a game on;
`KEY_PLAYCD`/`KEY_PLAY` map to nothing there. A third-party App ignores that key, so `abpadd`'s
`ResetWatch` reads every `/dev/input/event*` that can send it: a press bumps `SharedState::quitRequests`
(was `reserved[0]` - the block keeps its size and version, an older shim ignores it), the shim turns a
new count into a quit event at once, and the daemon sends SIGTERM at 1.5 s and SIGKILL at 3 s. An App
with `VirtualPad=false` (the terminal) gets `abpadd --exit-only` on the console (`[ -d /usr/sony ]` in
`app_env.sh`): no SDL, no shim, SIGTERM on the press. **Windows** has no abpad: an App there is left
through its own menu, which each port's readme names (the owner's choice).

Layout: `apps/abpad/src/core/` is `abpad_core`, which links **nothing** - not even `ab_core` - because
it ends up inside a shared object mapped into someone else's process; `src/daemon/` is `abpadd`;
`src/shim/` is the preload (`sdl_abi.h` spells out both SDLs' event structures rather than including a
header, since the shim is loaded into a process whose SDL we did not build); `src/padtest/` is
**`padtest`**, the instrument - a live panel drawn with terminal escapes, `--gc` for the controller
API, and **`--map`**, which asks for one control at a time and writes the gamecontrollerdb line itself
(the pscbios wizard's job, in the one place a Pi or a PC has no wizard). Tests in
`tests/apps/test_abpad_core.cpp`.

**`rc/app_env.sh` on both platforms** now starts the daemon (`--watch-pid`, so it goes when the App
goes), preloaded with its own environment: `LD_LIBRARY_PATH` = `/tmp/lib` on the console, and
`AB_PAD_DB` = the launcher's gamecontrollerdb (`/etc/autobleem/...` first, then
`<root>/Autobleem/bin/autobleem/gamecontrollerdb.txt`, as `Env::padMappingFiles()`), independent of
the App's own `LD_LIBRARY_PATH`/`AB_APP_LIB`. Abpadd's output falls back to
`${AB_RUNTIME_DIR:-/tmp/autobleem}/logs` when `AB_LOG_DIR` cannot be written, so a read-only stick does
not prevent the daemon from starting. `app_env.sh` also preloads the shim, points an App at
`rc/pad.default.ini` plus its own `Apps/<name>/pad.ini`, and gives the App **a home on the stick**:
`$HOME` is `<root>/Home` with the XDG variables under it, because an App left alone writes to
`/root/.local/share/...` - the machine's own storage, which is not ours to write to and does not travel
with the stick. Note that exFAT and FAT cannot hold a symlink, so a program wanting one under `$HOME`
(PulseAudio tries) logs a warning; harmless so far.

**Proven on a Pi 400** with five Apps built for it (not in this repository - see below): SDLPoP
(GameController API), OpenTyrian and OpenJazz (raw joystick), OpenJazz again built with `LEGACY_SDL=ON`
(the SDL 1.2 ABI, through sdl12-compat), and Chocolate Doom (both APIs plus a GUID lookup). **Not yet
run on a console.** Two lessons from getting there worth keeping: an App on an appliance must **ship
its configuration**, because there is no setup tool reachable from a launcher (Chocolate Doom's pad was
simply switched off in its own config, and Doom needs `joystick_index`/`joystick_guid` as well as
`use_joystick 1`); and when the shim seems to do nothing, **`LD_DEBUG=bindings`** names the object each
symbol bound to in one line, which is the first diagnostic and not the last.

The test Apps are deliberately **not** in this repository: Freedoom may be redistributed and the Jazz
Jackrabbit shareware may not, and neither question is settled by us building them. A fetch-and-build
recipe is the clean route if they are ever to ship.


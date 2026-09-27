# Writing a Store catalog

The **AutoBleem Store** is an [extension](extensions.md) that downloads and installs Apps and games. What it
offers comes from **catalogs**: plain tab-separated text files listing what is available and where to get
it. Anyone can publish one - drop a file where the Store looks for local sources, or point the Store at a
URL, and its entries show up alongside AutoBleem's own.

This page intentionally does not repeat the format itself, to avoid the two copies drifting apart. The
authoritative reference is the Store's own README:

**<https://github.com/autobleem2/ext_store#the-tsv-format>**

It covers the file format (the header line, one row per file, how multiple files become one item), what
each column means (`kind`, `title`, `url`, `size`, `sha256`, `disc`, `serial`, `image`, `version`,
`description`), which archive formats are supported, the optional integrity check (`size`/`sha256`), and how
a NoPayStation-style list is read as well as AutoBleem's own layout. It also covers how a catalog is added
by a player (a file under `sources/`, or a URL in the Store's Sources tab) and what pictures are shown for
an entry.

A short orientation, to know what you are looking at before you follow that link:

- **A catalog is not code.** It needs no build, no compiler, no repository of its own - just a text file
  you can host anywhere reachable over HTTP(S).
- **You are responsible for what your catalog contains** - what you link to, and that you have the right to
  distribute it. AutoBleem does not review third-party catalogs.
- The Store currently only installs two kinds of item from a catalog: a PS1 game (`ps1`) and a multi-platform
  App package (`app`, in the [App format](apps.md)). Anything else in a `kind` column is accepted as data but
  shown to the player as not installable.

If you run into something the README does not answer - a column whose exact behavior is unclear, or a case
it does not cover - please open an issue on
[`autobleem2/ext_store`](https://github.com/autobleem2/ext_store/issues) rather than guess: the README is
meant to be the complete reference, and a gap in it is a documentation bug worth fixing there.

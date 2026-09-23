# AutoBleem 2

A game launcher for the **PlayStation Classic** - and, from the same code, an appliance for the
**Raspberry Pi** and a **PC USB stick**, and a **Windows** program. Downloads, install guides and the user
manual: **https://autobleem.retromenele.pl/**

This repository is the project's hub: the map of the repositories, the rules they follow, the plans and
their history, and the checklist testers work from. The code is in the other repositories of
[github.com/autobleem2](https://github.com/autobleem2) (see [CLAUDE.md](CLAUDE.md) for which does what).

## Getting everything

```bash
git clone https://github.com/autobleem2/autobleem-main.git
cd autobleem-main
tools/workspace.sh --https     # clones every repository here (repos.txt), at develop
tools/workspace.sh status      # where each one stands
```

## For testers

[docs/tester-checklist.md](docs/tester-checklist.md) - what to test, what you should see, which logs to send.

## Licence

The AutoBleem code is GPL-3.0-or-later (each repository carries its `LICENSE`); the AutoBleem name, logo
and theme artwork are not part of that grant.

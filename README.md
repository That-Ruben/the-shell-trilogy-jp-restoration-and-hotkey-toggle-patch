# The Shell Trilogy (Kara no Shoujo) — Japanese Language Restoration

Restores the **Japanese text option** in the western (Shiravune) releases of
the Kara no Shoujo remasters — *The Shell Part I: Inferno*, *Part II:
Purgatorio* and *Part III: Paradiso* (Artemis engine).

The western releases still ship the complete Japanese script: every one of
the ~93,000 dialogue text blocks across the trilogy carries its Japanese
text alongside the English and Chinese. Only the option to display it was
removed. This project re-enables it:

- **Japanese as a 4th language** in Config → Language Select
- **Instant JP⇄EN toggle** with the **L** key, mid-scene, backlog included
- A small **JP toggle button** in the in-game button row
- The story text switches; menus stay in English (the releases contain no
  Japanese menu art)

## Installing the patches

Grab the [released zip](https://catbox.moe/c/67gbnl), then copy each file into that
game's folder, next to the game's `.exe`:

- `TheShell.pfs.080` — The Shell Part I: Inferno
- `TheShell2.pfs.080` — The Shell Part II: Purgatorio
- `TheShell3.pfs.080` — The Shell Part III: Paradiso

You can install any or all of them; the games are independent.
Uninstall: delete the file again. Saves are unaffected.

Built from and tested with the GOG releases. Steam and Jast versions
should be compatible.

## This repository

**No game data is distributed here** — only the toolchain and documentation
to build the patches from a game copy you own.

### Building it yourself

Requirements: one of the games, and Python 3.10+ with `Pillow`.

```
python tools/build_all.py "<GAME_DIR>"
```

Writes `dist/<base>.pfs.080` for whichever game the directory contains
(run it once per game). The build is deterministic — identical inputs
produce byte-identical patches.

### How it works (short version)

The Japanese text needs no restoring — it is already complete in every
script file. The patch therefore contains no script data at all, just the
handful of system files that expose the language:

- `build_all.py` — layers the game's pfs archives the way the engine does
  (last archive wins), adds the 日本語 button to the config language panel,
  binds the L key to a small toggle function appended to the engine's
  `lang.lua`, adds the JP button to the message-window button row, and
  marks the window title so patched installs are recognizable
- `edit_confbg.py` — draws the extra 日本語 row and the L-key hint onto the
  config background art; the three games share one panel layout with
  different skins, so colors and label style are sampled from each game's
  own art
- `make_langbtn.py` — generates the JP button sprite in each game's icon
  style, sampling the hover accent color (part 1 red, part 2 orange,
  part 3 cyan)
- `pfs.py` — reader/writer for Artemis pf6/pf8 archives

A one-line guard keeps the UI language unchanged while the text language
is Japanese, since the releases ship no Japanese UI art.

## Credits

Patch by **That-Ruben**. Tools are MIT-licensed (see LICENSE).

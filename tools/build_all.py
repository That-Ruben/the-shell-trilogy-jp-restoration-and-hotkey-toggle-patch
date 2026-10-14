"""Build <Game>.pfs.080 - Japanese language patch for the Kara no Shoujo
trilogy remasters "The Shell" (western/Shiravune releases, Artemis engine).

The western releases ship the complete Japanese script in every dialogue
block and the full ja engine wiring (langnum, lang_ja(), ja font metrics)
but expose no way to select it.  This patch only re-enables it:

  1. a 日本語 button (bt1013) in the config Language Select panel,
  2. the L key as an instant ja<->en toggle,
  3. an EN/JP toggle button in the small message-window button row,
  4. a guard so the UI language stays as-is while the text language is
     Japanese (no pc/ja/ UI art exists in these releases),
  5. the extra 日本語 row and L-key hint drawn onto the config background.

No other content is touched; every language's text stays byte-identical.

Usage:  python kns/tools/build_all.py <GAME_DIR> [OUT_PFS]

The game is identified by its base .pfs archive (TheShell.pfs,
TheShell2.pfs, ...); all its numbered patch archives are layered in order
(last wins) and the patch is built from the effective newest files.
The default output is kns/dist/<base>.pfs.080.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pfs import PfsArchive, write_pf8  # noqa: E402

import edit_confbg  # noqa: E402
import make_langbtn  # noqa: E402

OUT_SUFFIX = "080"

BT1013 = ('\t\tbt1013 = { name="bt1013", file="conf/btn", id="z.bt.04", '
          'x=1144, y=340, w=32, h=32, com="toggle", def="langnum", '
          'exec="config_toggle", p1="1", p2="bt1014|bt1015|bt1016", '
          'p3="ja", p4="conf_langchange", dir="height", cx="304", cy="64", '
          'cw="32", ch="32", clip="304,64,32,32", clip_a="304,96,32,32", '
          'clip_c="304,128,32,32", clip_d="304,160,32,32", },\r\n')

TOGGLE_FUNC = (
    "----------------------------------------\r\n"
    "-- JP restoration patch: instant ja<->en toggle (L key)\r\n"
    "function lang_toggle_jaen()\r\n"
    '\tadv_putlang(get_language(true) == "ja" and "en" or "ja")\r\n'
    "end\r\n"
)


def patch_lang_tbl(text, name):
    """Add the ja radio button to a list_windows_<lang>.tbl.

    bt1013 joins the langnum radio group; the existing buttons get it
    prepended to their p2 mutual-exclusion lists (whose exact contents
    vary between the games - part 3 carries stale entries)."""
    def add_excl(m):
        return m.group(1) + 'p2="bt1013|' + m.group(2) + '"'

    text, n = re.subn(
        r'(\t\tbt101[456] = \{ [^\n]*?)p2="(bt101[\d|bt]*)"', add_excl, text)
    if n != 3:
        raise SystemExit(f"{name}: expected 3 language buttons, patched {n}")
    anchor = "\t\tbt1014 = {"
    if text.count(anchor) != 1:
        raise SystemExit(f"{name}: bt1014 anchor not unique")
    return text.replace(anchor, BT1013 + anchor)


def patch_adv_groups(text, name):
    """Add the EN/JP toggle button to the small message-window button row
    (left of bt_selnext, same 23px pitch) in every adv button group
    (part 1 has two groups, part 2 has three)."""
    pat = re.compile(r'\t\tbt_selnext = \{ name="bt_selnext", file="mw/mw", '
                     r'id="mw\.(zt|bt)\.dc\.8"')

    def repl(m):
        prefix = m.group(1)
        line = (f'\t\tbt_lang = {{ name="bt_lang", file="mw/mwlang", '
                f'id="mw.{prefix}.dc.12", x=1154, y=646, w=21, h=32, '
                'com="btn", exec="lang_toggle_jaen", dir="height", '
                'cx="0", cy="0", cw="21", ch="32", clip="0,0,21,32", '
                'clip_a="0,32,21,32", clip_c="0,64,21,32", '
                'clip_d="0,96,21,32", },\r\n')
        return line + m.group(0)

    text, n = pat.subn(repl, text)
    if n < 2:
        raise SystemExit(f"{name}: expected >=2 bt_selnext anchors, got {n}")
    return text


def patch_main_tbl(text):
    """Bind the L key (code 76) to the language toggle in list_windows.tbl.

    Parts 1/2 use a compact one-line format, part 3 a pretty-printed one;
    both are handled."""
    if "[76]" in text:
        raise SystemExit("list_windows.tbl: key 76 already bound")
    m = re.search(r"advkey=\{\r?\ndef=\{", text)
    if m:  # compact
        text = text[:m.end()] + '[76]={btn="L",adv="LANG"},' + text[m.end():]
        old = 'tbl={CLICK="adv_click",'
        if text.count(old) != 1:
            raise SystemExit("list_windows.tbl: advkey tbl anchor not unique")
        return text.replace(
            old, 'tbl={LANG="lang_toggle_jaen",CLICK="adv_click",')
    m = re.search(r"advkey = \{\r\n\t\tdef = \{\r\n", text)  # pretty-printed
    if not m:
        raise SystemExit("list_windows.tbl: no advkey def anchor found")
    text = (text[:m.end()] + '\t\t\t[76] = { btn="L", adv="LANG" },\r\n'
            + text[m.end():])
    old = '\t\ttbl = {\r\n\t\t\tCLICK = "adv_click",'
    if text.count(old) != 1:
        raise SystemExit("list_windows.tbl: advkey tbl anchor not unique")
    return text.replace(
        old, '\t\ttbl = {\r\n\t\t\tLANG = "lang_toggle_jaen",\r\n'
             '\t\t\tCLICK = "adv_click",')


def patch_staff(text):
    """Staff roll text images exist only for en/cn/tw; the ja entry points
    at the empty staff/ root, so in Japanese the credits played as music
    over a black screen. Use the English credit images instead."""
    text, n = re.subn(r'(staff=\{\s*ja=)""', r'\1"en/"', text)
    if n != 1:
        raise SystemExit(f"list_windows.tbl: staff path entry found {n}x")
    return text


def patch_func_lua(text):
    """Mark the patch in the window title (func.lua uses LF endings)."""
    old = '\t\tif init.game_ver == "on" and v then tx = tx.." - Ver"..v end'
    if text.count(old) != 1:
        raise SystemExit("func.lua: caption version line not unique")
    return text.replace(
        old,
        old + '\n\t\ttx = tx.." - Japanese restoration patch by That-Ruben"')


def patch_lang_lua(text):
    """Keep the UI language unchanged when the text language becomes ja
    (there is no pc/ja/ UI art), and append the toggle function."""
    old = '\t\tif init.game_uilangsync == "on" then conf.ui_lang = ln end'
    if text.count(old) != 1:
        raise SystemExit("lang.lua: uilangsync line not unique")
    text = text.replace(
        old,
        '\t\tif init.game_uilangsync == "on" and ln ~= "ja" '
        "then conf.ui_lang = ln end")
    return text + TOGGLE_FUNC


def clean_ja_scripts(effective):
    """Strip leftover ＄ markers from the Japanese text.

    Part 2's ja strings retain string-initial full-width dollar signs
    (usually followed by a full-width space) from the original
    pre-remaster engine; the localizers deleted them from en/cn/tw but
    the untouched ja text still has them, and Artemis renders them
    literally.  They appear only in ja subtrees and only right after a
    string's opening quote (verified across all three games), so a plain
    byte replace is exact.  Games without them (parts 1 and 3) ship no
    script files at all."""
    marker = "＄".encode("utf-8")
    ms = '"＄　'.encode("utf-8")
    m = '"＄'.encode("utf-8")
    cleaned = []
    for key in sorted(effective):
        if not (key.startswith("script\\") and key.endswith(".ast")):
            continue
        an, a, e = effective[key]
        data = a.read(e)
        if marker not in data:
            continue
        fixed = data.replace(ms, b'"').replace(m, b'"')
        if marker in fixed:
            raise SystemExit(f"{e.name}: unexpected non-string-initial ＄")
        cleaned.append((e.name, fixed))
    return cleaned


def find_archives(game_dir):
    """The game's base .pfs plus its numbered patches, in load order,
    excluding this patch's own output suffix."""
    bases = [f for f in os.listdir(game_dir) if f.lower().endswith(".pfs")]
    if len(bases) != 1:
        raise SystemExit(f"expected one base .pfs in {game_dir}, "
                         f"found {bases}")
    base = bases[0]
    nums = []
    for f in os.listdir(game_dir):
        m = re.fullmatch(re.escape(base) + r"\.(\d+)", f)
        if m and m.group(1) != OUT_SUFFIX:
            nums.append((int(m.group(1)), f))
    return base, [base] + [f for _, f in sorted(nums)]


def main(game_dir, out_pfs=None):
    base, archives = find_archives(game_dir)
    if out_pfs is None:
        out_pfs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "dist", f"{base}.{OUT_SUFFIX}")
    print(f"game archives (load order): {archives}")

    # effective file set, last archive wins
    effective = {}
    for an in archives:
        a = PfsArchive(os.path.join(game_dir, an))
        for e in a.entries:
            effective[e.name.lower()] = (an, a, e)

    def read(name):
        try:
            an, a, e = effective[name.lower()]
        except KeyError:
            raise SystemExit(f"{name} not found in any archive")
        return a.read(e)

    out = []

    # 1. per-language tbls: ja config button + in-game toggle button
    for tbl in ("system\\table\\list_windows_en.tbl",
                "system\\table\\list_windows_cn.tbl",
                "system\\table\\list_windows_tw.tbl",
                "system\\table\\list_windows_ja.tbl"):
        text = read(tbl).decode("utf-8")
        text = patch_lang_tbl(text, tbl)
        text = patch_adv_groups(text, tbl)
        out.append((tbl, text.encode("utf-8")))

    # 2. main tbl: L-key binding, ja staff roll images
    text = read("system\\table\\list_windows.tbl")
    out.append(("system\\table\\list_windows.tbl",
                patch_staff(patch_main_tbl(text.decode("utf-8")))
                .encode("utf-8")))

    # 3. lang.lua: ui-language guard + toggle function
    text = read("system\\msg\\lang.lua")
    out.append(("system\\msg\\lang.lua",
                patch_lang_lua(text.decode("utf-8")).encode("utf-8")))

    # 3b. func.lua: patch marker in the window title
    text = read("system\\adv\\func.lua")
    out.append(("system\\adv\\func.lua",
                patch_func_lua(text.decode("utf-8")).encode("utf-8")))

    # 3c. scripts with leftover ＄ markers in the ja text (part 2)
    cleaned = clean_ja_scripts(effective)
    if cleaned:
        print(f"cleaning ＄ markers from {len(cleaned)} scripts")
        out.extend(cleaned)

    # 4. config background art: 日本語 row + L-key hint
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        font_path = os.path.join(tmp, "font.otf")
        with open(font_path, "wb") as f:
            f.write(read("font\\sourcehanserif-medium.otf"))
        for ln in ("en", "cn", "tw"):
            name = f"pc\\{ln}\\conf\\bg01.png"
            src = os.path.join(tmp, f"bg01_{ln}.png")
            dst = os.path.join(tmp, f"bg01_{ln}_out.png")
            with open(src, "wb") as f:
                f.write(read(name))
            edit_confbg.edit(src, dst, font_path)
            with open(dst, "rb") as f:
                out.append((name, f.read()))

        # 5. sprite for the in-game EN/JP toggle button (hover accent
        #    color is sampled from the game's own mw sprite sheet)
        bold_path = os.path.join(tmp, "bold.otf")
        with open(bold_path, "wb") as f:
            f.write(read("font\\sourcehanserif-bold.otf"))
        mw_path = os.path.join(tmp, "mw.png")
        with open(mw_path, "wb") as f:
            f.write(read("pc\\en\\mw\\mw.png"))
        sprite_path = os.path.join(tmp, "mwlang.png")
        make_langbtn.make(bold_path, sprite_path, mw_path)
        with open(sprite_path, "rb") as f:
            sprite = f.read()
        for ln in ("en", "cn", "tw"):
            out.append((f"pc\\{ln}\\mw\\mwlang.png", sprite))

    out_pfs = os.path.normpath(out_pfs)
    os.makedirs(os.path.dirname(out_pfs) or ".", exist_ok=True)
    write_pf8(out_pfs, out)
    print(f"wrote {out_pfs} ({os.path.getsize(out_pfs)} bytes, "
          f"{len(out)} files)")

    # read-back verification
    a = PfsArchive(out_pfs)
    got = {e.name: a.read(e) for e in a.entries}
    assert len(got) == len(out)
    for name, data in out:
        assert got[name] == data, name
    assert b'p3="ja"' in got["system\\table\\list_windows_en.tbl"]
    assert (b'[76]={btn="L",adv="LANG"}' in got["system\\table\\list_windows.tbl"]
            or b'[76] = { btn="L", adv="LANG" }'
            in got["system\\table\\list_windows.tbl"])
    assert re.search(rb'staff=\{\s*ja="en/"',
                     got["system\\table\\list_windows.tbl"])
    assert b"lang_toggle_jaen" in got["system\\msg\\lang.lua"]
    assert b"Japanese restoration patch" in got["system\\adv\\func.lua"]
    assert got["system\\table\\list_windows_en.tbl"].count(b'name="bt_lang"') >= 2
    assert got["pc\\en\\mw\\mwlang.png"] == sprite
    for n, _ in out:
        if n.lower().startswith("script\\"):
            assert "＄".encode("utf-8") not in got[n], n
    print("read-back verification OK")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

"""gen_contracts.py — regenerate the author files' field tables from their declarations (gate sheet-contract).

Each author file's fields are declared once, in the engine (`src/engine/contracts_sheet.py` for the character
sheet). The blueprints carry those declarations as a table between two markers, and this writes it:

    <!-- GENERATED: contracts_sheet -->
    ...rows...
    <!-- END GENERATED -->

Everything outside the markers - what a field is FOR, the traps, the worked examples - stays hand-written. The
table was the part that rotted: the character blueprint marked drives.orientation REQUIRED after the engine
stopped reading it, and said "the same eight names" of a mood with nine paths.

`--check` exits non-zero when a blueprint's table disagrees with the declarations; `tests/test_contracts_sheet.py`
runs it, so the table cannot drift without the suite going red.
"""
import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from src.engine import contracts                                       # noqa: E402
from src.engine import contracts_sheet                                 # noqa: E402
from src.engine import contracts_world                                 # noqa: E402
from src.engine import contracts_scene                                 # noqa: E402

# which declarations go into which blueprint
TARGETS = (("contracts_sheet", contracts_sheet.SHEET, os.path.join(REPO, "docs", "authoring", "BLUEPRINT-character.md")),
           ("contracts_world", contracts_world.WORLD, os.path.join(REPO, "docs", "authoring", "BLUEPRINT-world.md")),
           ("contracts_scene", contracts_scene.SCENE, os.path.join(REPO, "docs", "authoring", "BLUEPRINT-scene.md")))


def region(name):
    return re.compile(r"(<!-- GENERATED: %s -->\n)(.*?)(<!-- END GENERATED -->)" % re.escape(name), re.S)


def render(text, name, fields):
    """-> the text with its generated region rewritten, or None when it has no markers for `name`."""
    rx = region(name)
    if not rx.search(text):
        return None
    return rx.sub(lambda m: m.group(1) + contracts.table(fields) + "\n" + m.group(3), text, count=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if a blueprint's table disagrees with the declarations")
    args = ap.parse_args(argv)
    stale = []
    for name, fields, path in TARGETS:
        with io.open(path, encoding="utf-8") as fh:
            text = fh.read()
        new = render(text, name, fields)
        if new is None:
            print("%s: no GENERATED: %s markers" % (os.path.relpath(path, REPO), name))
            stale.append(path)
            continue
        if new != text:
            if args.check:
                stale.append(path)
                print("%s: the %s table disagrees with the declarations - run scripts/gen_contracts.py"
                      % (os.path.relpath(path, REPO), name))
            else:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
                print("%s: %s table written (%d fields)" % (os.path.relpath(path, REPO), name, len(fields)))
    if args.check and not stale:
        print("the field tables match their declarations")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())

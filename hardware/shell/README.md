# Shell generator

`shell.py` generates the two printed halves of the Releaf shell as STEP files in this folder:

| File | What it is |
| --- | --- |
| `releaf-shell-back.step` | Back half, against the wall. It clips onto the linker and holds the board. Also contains a loose support block. |
| `releaf-shell-front.step` | Front half, the cover you see, with the logo leaf as separate bodies. |
| `releaf-shell.3mf` | Bambu Studio project with both halves set up for printing. |

It only needs CadQuery 2.x:

```sh
python hardware/shell/shell.py
```

The logo inlay is read from `logo.svg` in the repository root.

## Printing

Both STEP files are already oriented for printing. Import each one as a single object with multiple parts.
- The back half prints with its back face down. Its support block fills the linker recess and sticks out of both long sides as a tab. After printing, push it out from one side or pull it from the other.
- The front half prints with its front face down, so the front picks up the build plate's texture. The logo is indented 0.4 mm into the front face. The floor of the indent is the logo's own bodies (the next 0.4 mm), so give them any filament, or the front's filament for a plain engraving.
- No slicer supports are needed. Every top bevel is 45° or less.

## Assembly

1. Drop the board into the back half, pads first. The four pins locate it by its edge notches.
2. Press the front half on until both latches click, one at each angled end. There are no screws.

To open it, pull the halves apart firmly; the 45° catches let go. For a gentler release, press each hook toward the middle of the shell through the opening at each angled end of the back face. If a hook ever breaks off, it falls out through that opening. The switch and USB-C port are inside, so open the shell to reach them.

## Settings

All in `shell.py`:
- Latch fit: `HOOK` (catch depth) and `PRELOAD` (how hard the latches pull the halves together).
- Board fit along the panel side: `CLEAR_JOINT`.
- Logo: `LOGO_H` (size) and `LOGO_Y` (position).
- Component heights: `MINI_STANDOFF`, `REG_STANDOFF`, `CAP_LIFT`. These assume the SuperMini and the regulator sit on standard 2.54 mm headers and C1 lies flat.
- Room under the board: the back plate is 1 mm thick (`PLATE_FRONT`), leaving about 4 mm for solder joints and pin ends.

The shell is 17.2 mm thick. The 8 mm capacitor sets that height.

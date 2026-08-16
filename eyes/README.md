# eyes/

`eyes-idle.svg` is the image at the top of the profile README: a figure on the
rim of a canyon, and two glowing eyes watching him. It loops on its own — CSS
keyframes, no `<script>`, because GitHub strips that from Markdown.

Clicking it swaps in `eyes-click.svg` for 12 seconds — the piano falls, and
something looks back. Its eyes are on the same blink loop, so it never ends on
a dead frame; the last frame it holds is identical to the idle one. That swap
is done by
[readme-onclick-animation](https://github.com/qvd808/readme-onclick-animation).

**The source lives on the [`eyes-readme`](https://github.com/qvd808/qvd808/tree/eyes-readme/eyes) branch:**
the interactive sandbox (`index.html`, where the eyes actually follow your
cursor), the captured frame both files are drawn on, and the two builds that
generate the files next to this one.

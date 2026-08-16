# eyes/

`eyes-idle.svg` is the image at the top of the profile README: a figure on the
rim of a canyon, and two glowing eyes watching him. It loops on its own — CSS
keyframes, no `<script>`, because GitHub strips that from Markdown.

Clicking it swaps in `eyes-once.svg` for 12 seconds — the piano falls, and
something looks back — then it returns here. That swap is done by
[readme-onclick-animation](https://github.com/qvd808/readme-onclick-animation).

**The source lives on the [`eyes-readme`](https://github.com/qvd808/qvd808/tree/eyes-readme/eyes) branch:**
the interactive sandbox (`index.html`, where the eyes actually follow your
cursor), the captured frame both assets are drawn on, and `build_idle.py`,
which generates the file next to this one.

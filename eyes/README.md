# Eyes

The scene behind the image at the top of the profile README: a figure on the
rim of a canyon, two glowing eyes watching him, and — if you click — a piano.

| file | what it is |
| --- | --- |
| `index.html` | the design sandbox. Full scene, eyes track the cursor, click to run the calamity. Not what the README uses. |
| `scene-base.jpg` | one captured frame of the sketch, before anything falls. Both README assets are drawn on it. |
| `build_idle.py` | builds `eyes-idle.svg` from `scene-base.jpg` |
| `eyes-idle.svg` | **the idle loop the README shows**: the eyes stare at the figure and blink, forever |
| `make_face.py` | crops the reference art into `face_asset.json` for the reveal at the end |
| `build.py` | folds the sandbox scene + face asset into a single-file `index.html` |

Run the sandbox locally:

```bash
cd eyes
python3 -m http.server 8000   # then open http://localhost:8000
```

Rebuild the idle loop (also fine to open `eyes-idle.svg` directly in a browser
to check it):

```bash
python3 build_idle.py
```

## How the README image works

GitHub strips `<script>` and `<iframe>` from rendered Markdown, so `index.html`
cannot run in a README — only `<img>` survives. So the README image is served
by [readme-onclick-animation](https://github.com/qvd808/readme-onclick-animation):

* **idle** — `/scene` streams `eyes-idle.svg`, a looping CSS animation. The eyes
  hold a stare on the figure and blink on an uneven schedule. No cursor
  tracking; an `<img>` gets no mouse.
* **clicked** — the link goes to `/play`, which flags the click in Redis and
  bounces straight back to the profile. For the next 12 seconds `/scene` streams
  `eyes-once.svg` instead: the piano falls, the figure is gone, something looks
  back. Then it returns to the idle loop.

Both files are built on the same `scene-base.jpg`, so the swap has nothing to
cross-fade — the cliff, the sky and the stars sit on identical pixels and only
the eyes ever move.

The `still` and `play` URLs must point at an allowed host (`raw.githubusercontent.com`),
so `eyes-idle.svg` has to be committed on the **default branch** before the
profile README can find it.

# Eyes

The scene behind the image at the top of the profile README: a figure on the
rim of a canyon, two glowing eyes watching him, and — if you click — a piano.

| file | what it is |
| --- | --- |
| `index.html` | the design sandbox. Full scene, eyes track the cursor, click to run the calamity. Not what the README uses. |
| `scene-base.jpg` | one captured frame of the sketch, before anything falls |
| `scene.py` | eye geometry, blink schedule, and the encoded background — shared by both builds |
| `build_idle.py` | → `eyes-idle.svg`, **the idle loop**: the eyes stare at the figure and blink, forever |
| `once-source.svg` | the calamity build from readme-onclick-animation, used as input |
| `build_click.py` | → `eyes-click.svg`, **the click animation**: same calamity, but the eyes never stop blinking |
| `make_face.py` | crops the reference art into `face_asset.json` for the reveal at the end |
| `build.py` | folds the sandbox scene + face asset into a single-file `index.html` |

```bash
python3 build_idle.py && python3 build_click.py   # rebuild both README assets
python3 -m http.server 8000                       # or poke at index.html
```

Opening `eyes-idle.svg` / `eyes-click.svg` straight in a browser is the fastest
way to check them.

## How the README image works

GitHub strips `<script>` and `<iframe>` from rendered Markdown, so `index.html`
cannot run in a README — only `<img>` survives. So the image is served by
[readme-onclick-animation](https://github.com/qvd808/readme-onclick-animation):

* **idle** — `/scene` streams `eyes-idle.svg`. The eyes hold a stare on the
  figure and blink on an uneven schedule. No cursor tracking; an `<img>` gets
  no mouse.
* **clicked** — the link goes to `/play`, which flags the click in Redis and
  bounces back to the profile (at `#user-content-eyes`, so you land on the
  scene). For the next 12 seconds `/scene` streams `eyes-click.svg`: the piano
  falls, the figure is gone, something looks back.

## Why the click build exists

The upstream calamity is `animation: 6.95s linear 1 forwards` — it plays once
and holds. That is right for a page you can click again and wrong for a README:
when the server's 12-second window expires, **nothing re-requests the image**.
The `<img>` is already loaded, so the visitor keeps staring at a frozen last
frame with dead eyes until they reload.

`build_click.py` patches the eyes onto the same infinite blink loop the idle
file uses, and leaves the calamity untouched. They blink while the piano falls,
fade out under the face, and are still blinking when the reveal ends — there is
no dead state left to end in. The final held frame is then pixel-identical to
the idle loop, so the eventual swap back is invisible.

Both files embed the same `scene-base.webp`, re-encoded once and shared, so the
swap has nothing to cross-fade. WebP rather than the source JPEG because
`/scene` sends `no-store` — every profile view pays for the whole file — and it
halves the idle asset (211 KB → 122 KB) at a mean error under 2/255, grain
intact.

The `still` and `play` URLs must point at an allowed host
(`raw.githubusercontent.com`), so both built files have to be committed on the
**default branch** before the profile README can find them.

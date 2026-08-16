"""Build eyes-click.svg - what the README shows for 12s after a click.

The upstream build (once-source.svg, from readme-onclick-animation) plays the
calamity once and stops: `animation: 6.95s linear 1 forwards`. That is the
right behaviour for a page you can click again, and the wrong behaviour for a
README. Nothing re-requests the image when the server's 12s window expires -
the <img> is already loaded - so the visitor is left staring at a frozen final
frame with dead eyes until they reload the page.

So this patches two things and leaves the calamity itself untouched:

  1. the eyes get the shared blink loop instead of the one-shot wandering
     gaze, running infinitely. They are blinking while the piano falls, they
     fade out under the face like before, and when the reveal ends they are
     still blinking - the animation has no dead state to end in.

  2. the background is re-encoded to WebP, the same bytes build_idle.py
     embeds, which halves a file that is delivered uncached on every view.

Run:  python3 build_click.py   ->  eyes-click.svg
"""
import pathlib
import scene as S

here = pathlib.Path(__file__).parent
svg = (here / "once-source.svg").read_text()


def sub(old, new, why):
    global svg
    assert svg.count(old) == 1, f"FAILED ({why}): {svg.count(old)} matches"
    svg = svg.replace(old, new)
    print(f"  patched: {why}")


# --- 1. the eyes ---------------------------------------------------------
# .s already declares `animation:6.95s linear 1 forwards` and view-box
# transforms; these selectors come later in the sheet, so they win on both.
sub(".halo{animation-name:gazeH}.iris{animation-name:gazeI}",
    S.eye_css().replace("\n", ""),
    "one-shot gaze -> shared infinite blink")

# gazeH/gazeI are the last two keyframe blocks before the reduced-motion
# guard, and nothing references them now
_a = svg.index("@keyframes gazeH{")
_b = svg.index("@media(prefers-reduced-motion")
print(f"  patched: dropped gazeH/gazeI ({_b - _a:,} chars of dead keyframes)")
svg = svg[:_a] + svg[_b:]

# --- 2. the background ---------------------------------------------------
_i = svg.index('href="data:image/jpeg;base64,')
_j = svg.index('"', _i + 6)
old_uri = svg[_i + 6:_j]
new_uri = S.base_data_uri()
svg = svg[:_i + 6] + new_uri + svg[_j:]
print(f"  patched: background jpeg -> webp "
      f"({len(old_uri):,} -> {len(new_uri):,} chars)")

# the credit block names the file it was generated from; keep it honest
sub("README build of eyes/index.html - same scene, same beats, no cursor.",
    "README build of eyes/index.html - same scene, same beats, no cursor.\n"
    "  Eyes re-animated by eyes/build_click.py so the loop never ends.",
    "note the rebuild in the credit block")

out = here / "eyes-click.svg"
out.write_text(svg)
print(f"\nwrote {out.name}: {len(svg):,} bytes "
      f"(was {len((here / 'once-source.svg').read_text()):,})")

"""Build eyes-idle.svg - the looping idle asset for the profile README.

readme-onclick-animation serves this file from /scene while nobody has
clicked, and swaps to eyes-click.svg for 12s after a click.

GitHub strips <script> from Markdown, so the loop has to be declarative -
CSS keyframes on the two glow circles. They hold a stare on the figure at
the rim (a slow drift keeps it from looking frozen) and blink on a slightly
uneven schedule, because evenly spaced blinks read as a machine.

Everything about how the eyes behave lives in scene.py, shared with the
click build so the two files agree.

Run:  python3 build_idle.py   ->  eyes-idle.svg
"""
import pathlib
import scene as S

eyes = "\n".join(
    '<g transform="translate(%.3f,%.3f)">'
    '<circle class="halo" r="%.2f" fill="url(#gh)" filter="url(#bh)"/>'
    '<circle class="iris" r="%.2f" fill="url(#gi)" filter="url(#bi)"/></g>'
    % (x, y, S.HALO_R, S.IRIS_R) for x, y in S.EYES)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S.W} {S.H}" width="{S.W}" height="{S.H}" role="img" aria-label="A sketched figure stands at the rim of a canyon at night while two glowing eyes watch it and blink">
{S.CREDIT}
<defs>
{S.GRADIENTS}
<style>{S.eye_css()}
@media(prefers-reduced-motion:reduce){{.halo,.iris{{animation:none}}}}</style>
</defs>
<rect width="{S.W}" height="{S.H}" fill="{S.BG}"/>
<image href="{S.base_data_uri()}" x="0" y="0" width="{S.W}" height="{S.H}"/>
{eyes}
</svg>
"""

out = pathlib.Path(__file__).parent / "eyes-idle.svg"
out.write_text(svg)
print(f"wrote {out.name}: {len(svg):,} bytes  ({len(S.samples())} keyframes x2, {S.T}s loop)")
print(f"  gaze aim {S.AIM[0]:+.3f},{S.AIM[1]:+.3f} -> figure at {S.FIGURE}")
print(f"  blinks at {', '.join('%.2fs' % b for b in S.BLINKS)}")

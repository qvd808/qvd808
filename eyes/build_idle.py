"""Build eyes-idle.svg - the looping idle asset for the profile README.

readme-onclick-animation serves this file from /scene while nobody has
clicked, then swaps to eyes-once.svg (piano, wreck, face) for 12s after a
click. Both are drawn on the same captured frame, scene-base.jpg, so the
swap has nothing to cross-fade: the cliff, the sky and the figure sit on
exactly the same pixels in both files and only the eyes ever move here.

GitHub strips <script> from Markdown, so the loop has to be declarative -
CSS keyframes on the two glow circles. They hold a stare on the figure at
the rim (a slow drift keeps it from looking frozen) and blink on a slightly
uneven schedule, because evenly spaced blinks read as a machine.

The scene, the eye geometry and the gradients come from index.html; the
keyframes are sampled from the gaze/blink functions below rather than
captured, so this file is the whole animation.

Run:  python3 build_idle.py   ->  eyes-idle.svg
"""
import base64, math, pathlib

W, H = 1100, 520
BG = "#0b0c0e"
T = 7.2                                  # loop length, seconds

# --- geometry, straight out of the scene render (see index.html syncEyes) ---
EYES = [(662.373, 400.115), (810.873, 400.115)]
HALO_R, IRIS_R = 43.06, 24.34
HALO_BLUR, IRIS_BLUR = 8.05, 10.67
SOCKET = 2 * HALO_R / 0.92               # halo is 0.92 of the socket box
K_HALO, K_IRIS = SOCKET * 0.35, SOCKET * 0.65   # gaze travel; the iris outruns the halo

# the head of the figure standing on the rim - what the eyes are looking at
FIGURE = (414.0, 239.0)

# --- blink schedule: one, a double take, one more ---
BLINKS = [1.05, 3.40, 3.72, 5.85]
CLOSE, SHUT, OPEN = 0.075, 0.035, 0.115  # seconds; shutting is faster than opening
DUR = CLOSE + SHUT + OPEN


def smoothstep(x):
    return x * x * (3 - 2 * x)


def openness(t):
    """1 = wide open, 0 = shut. Blinks never overlap, so the lowest wins."""
    o = 1.0
    for b in BLINKS:
        d = t - b
        if d < 0 or d > DUR:
            continue
        if d < CLOSE:
            v = 1 - smoothstep(d / CLOSE)
        elif d < CLOSE + SHUT:
            v = 0.0
        else:
            v = smoothstep((d - CLOSE - SHUT) / OPEN)
        o = min(o, v)
    return o


_cx = sum(e[0] for e in EYES) / len(EYES)
_cy = sum(e[1] for e in EYES) / len(EYES)
_dx, _dy = FIGURE[0] - _cx, FIGURE[1] - _cy
_d = math.hypot(_dx, _dy)
AIM = (_dx / _d, _dy / _d)               # unit vector, eyes -> figure
PERP = (-AIM[1], AIM[0])


def gaze(t):
    """Locked on the figure. The lean-in and the sideways drift are small on
    purpose - this should read as being watched, not as a wandering eye."""
    w = 2 * math.pi * t / T
    lean = 0.30 + 0.030 * math.sin(w)            # along the line of sight
    drift = 0.022 * math.sin(2 * w + 1.0)        # across it
    return (AIM[0] * lean + PERP[0] * drift,
            AIM[1] * lean + PERP[1] * drift)


def samples():
    """Coarse where only the gaze moves, fine through every blink."""
    ts = {i * T / 24 for i in range(25)}
    for b in BLINKS:
        n = int(round((DUR + 0.06) / 0.015))
        ts |= {min(T, max(0.0, b - 0.03 + i * 0.015)) for i in range(n + 1)}
    return sorted(ts)


def keyframes(name, k, min_scale, opacity_floor):
    out = [f"@keyframes {name}{{"]
    for t in samples():
        o = openness(t)
        gx, gy = gaze(t)
        s = min_scale + (1 - min_scale) * o
        a = opacity_floor + (1 - opacity_floor) * o
        out.append("%.4f%%{transform:translate(%.2fpx,%.2fpx) scaleY(%.4f);opacity:%.3f}"
                   % (t / T * 100, k * gx, k * gy, s, a))
    out.append("}")
    return "".join(out)


CREDIT = """<!--
  ==========================================================================
  Idle loop for https://github.com/qvd808 - built by eyes/build_idle.py.
  Click-to-play is https://github.com/qvd808/readme-onclick-animation

  CREDIT / ATTRIBUTION - hidden easter egg

  The character revealed by the click animation is WONDER OF U, from
  "JoJo's Bizarre Adventure" (Part 8: JoJolion).

  JoJo's Bizarre Adventure and all of its characters are
  copyright (c) Hirohiko Araki / Shueisha.

  Reference image source:
    https://jojo.fandom.com/wiki/Wonder_of_U

  Used here as a non-commercial personal easter egg on a personal profile
  page. All rights in the character and its depiction remain with the
  original creator and rights holders. No affiliation with, sponsorship by,
  or endorsement from the rights holders is implied.

  Full respect and credit to Hirohiko Araki as the creator.
  ==========================================================================
-->"""

GRADIENTS = """<radialGradient id="gh" r="0.5"><stop offset="0.0" stop-color="rgb(207,232,255)" stop-opacity="1.0000"/><stop offset="0.3111" stop-color="rgb(125,180,245)" stop-opacity="1.0000"/><stop offset="0.6364" stop-color="rgb(58,111,184)" stop-opacity="1.0000"/><stop offset="0.8768" stop-color="rgb(32,74,140)" stop-opacity="0.4200"/><stop offset="1.0" stop-color="rgb(28,65,125)" stop-opacity="0.2168"/></radialGradient>
<radialGradient id="gi" r="0.5"><stop offset="0.0" stop-color="rgb(255,255,255)" stop-opacity="1.0000"/><stop offset="0.4243" stop-color="rgb(234,246,255)" stop-opacity="1.0000"/><stop offset="0.7778" stop-color="rgb(200,230,255)" stop-opacity="0.5000"/><stop offset="1.0" stop-color="rgb(176,214,255)" stop-opacity="0.1072"/></radialGradient>
<filter id="bh" x="-150%%" y="-150%%" width="400%%" height="400%%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="%.2f"/></filter>
<filter id="bi" x="-150%%" y="-150%%" width="400%%" height="400%%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="%.2f"/></filter>""" % (HALO_BLUR, IRIS_BLUR)

here = pathlib.Path(__file__).parent
b64 = base64.b64encode((here / "scene-base.jpg").read_bytes()).decode()

# fill-box keeps each circle's own centre as the scale origin, so a blink
# squashes the glow in place no matter where the gaze has pushed it
css = ("""/* one creature, so both eyes run the same clock */
.g{transform-box:fill-box;transform-origin:center;animation:%.2fs linear infinite;will-change:transform,opacity}
.halo{animation-name:eyeH}.iris{animation-name:eyeI}
@media(prefers-reduced-motion:reduce){.g{animation:none}}
""" % T
       + keyframes("eyeH", K_HALO, 0.060, 0.35)
       + keyframes("eyeI", K_IRIS, 0.040, 0.25))

eyes = "\n".join(
    '<g transform="translate(%.3f,%.3f)">'
    '<circle class="g halo" r="%.2f" fill="url(#gh)" filter="url(#bh)"/>'
    '<circle class="g iris" r="%.2f" fill="url(#gi)" filter="url(#bi)"/></g>'
    % (x, y, HALO_R, IRIS_R) for x, y in EYES)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="A sketched figure stands at the rim of a canyon at night while two glowing eyes watch it and blink">
{CREDIT}
<defs>
{GRADIENTS}
<style>{css}</style>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<image href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{W}" height="{H}"/>
{eyes}
</svg>
"""

out = here / "eyes-idle.svg"
out.write_text(svg)
print(f"wrote {out.name}: {len(svg):,} bytes  ({len(samples())} keyframes x2, {T}s loop)")
print(f"  gaze aim {AIM[0]:+.3f},{AIM[1]:+.3f} -> figure at {FIGURE}")
print(f"  blinks at {', '.join('%.2fs' % b for b in BLINKS)}")

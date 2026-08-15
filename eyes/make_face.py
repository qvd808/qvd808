"""Crop the Wonder of U reference to just the head, level its eye line, key out
the white background, and fade the bottom into darkness.
Character (c) Hirohiko Araki / Shueisha - see credit block in index.html."""
from PIL import Image, ImageFilter
from collections import deque
import base64, json, math, os

SRC = 'wonder-of-u.webp'
BOX = (60, 2, 166, 104)          # head box in source pixels

def detect_eyes(im):
    """the mask's two eyes are the only pink (b>g, red-dominant) blobs up top"""
    W, H = im.size; px = im.load(); hits = []
    for y in range(int(H*0.10), int(H*0.24)):
        for x in range(W):
            r, g, b = px[x, y][:3]
            if r > 95 and b > g + 3 and (r - g) > 35: hits.append((x, y))
    cl = []
    for x, y in hits:
        for c in cl:
            if abs(c['sx']/c['n']-x) < 10 and abs(c['sy']/c['n']-y) < 10:
                c['sx'] += x; c['sy'] += y; c['n'] += 1; break
        else: cl.append({'sx': x, 'sy': y, 'n': 1})
    cl = sorted([c for c in cl if c['n'] >= 10], key=lambda c: c['sx']/c['n'])
    return [(c['sx']/c['n'], c['sy']/c['n']) for c in (cl[0], cl[-1])]

src = Image.open(SRC).convert('RGB')
L, R = detect_eyes(src)
mid = ((L[0]+R[0])/2, (L[1]+R[1])/2)
deg = math.degrees(math.atan2(R[1]-L[1], R[0]-L[0]))
best = None
for cand in (deg, -deg):                      # pick the sign that levels the eyes
    rot = src.rotate(cand, resample=Image.BICUBIC, center=mid, fillcolor=(255,255,255))
    l2, r2 = detect_eyes(rot)
    if best is None or abs(r2[1]-l2[1]) < abs(best[3][1]-best[2][1]):
        best = (cand, rot, l2, r2)
deg, src, L, R = best
print(f"levelled by {deg:+.3f} deg -> eye dy now {R[1]-L[1]:+.3f}px (was {0.80:+.2f})")

crop = src.crop(BOX); w, h = crop.size; px = crop.load()
def isbg(p): return p[0] >= 225 and p[1] >= 225 and p[2] >= 225
bg = [[False]*h for _ in range(w)]; q = deque()
for x in range(w):
    for y in (0, h-1):
        if isbg(px[x, y]) and not bg[x][y]: bg[x][y] = True; q.append((x, y))
for y in range(h):
    for x in (0, w-1):
        if isbg(px[x, y]) and not bg[x][y]: bg[x][y] = True; q.append((x, y))
while q:
    x, y = q.popleft()
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x+dx, y+dy
        if 0 <= nx < w and 0 <= ny < h and not bg[nx][ny] and isbg(px[nx, ny]):
            bg[nx][ny] = True; q.append((nx, ny))
alpha = Image.new('L', (w, h), 255); ap = alpha.load()
for x in range(w):
    for y in range(h):
        if bg[x][y]: ap[x, y] = 0
alpha = alpha.filter(ImageFilter.MinFilter(3))          # erode 1px: kill white fringe
alpha = alpha.filter(ImageFilter.GaussianBlur(0.35))
ap = alpha.load()
F0 = int(h*0.80)
for y in range(F0, h):
    k = 1.0 - (y-F0)/max(1, h-F0)
    for x in range(w): ap[x, y] = int(ap[x, y]*k*k)
out = crop.convert('RGBA'); out.putalpha(alpha)
out.save('face_final.webp', 'WEBP', quality=88, method=6)
b64 = base64.b64encode(open('face_final.webp','rb').read()).decode()
eyes = {'lx': (L[0]-BOX[0])/w, 'ly': (L[1]-BOX[1])/h,
        'rx': (R[0]-BOX[0])/w, 'ry': (R[1]-BOX[1])/h}
json.dump({'b64': b64, 'eyes': eyes, 'w': w, 'h': h}, open('face_asset.json','w'))
print(f"crop {w}x{h}  webp {os.path.getsize('face_final.webp')} bytes  base64 {len(b64)} chars")
print("eyes:", {k: round(v, 5) for k, v in eyes.items()})

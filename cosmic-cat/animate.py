import cv2, numpy as np, subprocess, sys
src = cv2.imread(sys.argv[1]).astype(np.float32)
OUT = sys.argv[2]
H, W = src.shape[:2]
FPS, SEC = 30, 8
N = FPS*SEC
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rng = np.random.default_rng(7)

def ss(e0, e1, x):
    t = np.clip((x-e0)/(e1-e0), 0, 1); return t*t*(3-2*t)

# --- masks ---
r = np.sqrt(((xx-895)/300)**2 + ((yy-350)/290)**2)
cat = ss(1.0, 0.72, r) * ss(625, 575, yy)            # cat + nearby glow, fades above stones
stones = np.zeros((H,W), np.float32)
for (cx,cy,ax,ay) in [(890,655,120,45),(672,702,120,52),(1035,600,65,28),(1152,565,55,22),
                      (1200,537,40,14),(842,715,25,14),(460,745,75,35)]:
    stones = np.maximum(stones, ss(1.15, 0.8, np.sqrt(((xx-cx)/ax)**2+((yy-cy)/ay)**2)))
river = ss(440, 540, yy + 0.08*(xx-700))             # lower band, slightly tilted
free = (1-cat)

def rot_field(px, py, ang, w):
    dx, dy = xx-px, yy-py
    c, s = np.cos(ang), np.sin(ang)
    return w*((c*dx - s*dy) - dx), w*((s*dx + c*dy) - dy)

# arm weights: ramp outward from shoulder, band around the arm line
def arm_w(px, py, hx, hy, side):
    L = abs(hx-px)
    along = side*(px-xx)                              # >0 going out toward the hand
    ramp = ss(0, L*0.55, along) * ss(L+90, L+30, along)
    liney = py + (hy-py)*np.clip(along/L, 0, 1.3)
    band = np.exp(-((yy-liney)/42)**2)
    return ramp*band
wL = arm_w(800, 338, 705, 302, +1)
wR = arm_w(945, 330, 1075, 308, -1)
# tail weight
tdist = np.sqrt((xx-990)**2 + (yy-490)**2)
wT = ss(15, 90, tdist) * ss(1000, 1040, xx) * ss(330, 365, yy) * ss(545, 505, yy) * ss(1215, 1185, xx)

# stars for twinkling
g = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
hi = np.clip(g - cv2.GaussianBlur(g, (0,0), 4), 0, 255)
star = (hi > 28).astype(np.float32) * free
star = cv2.GaussianBlur(star, (0,0), 1.5)
hi_w = cv2.GaussianBlur(hi, (0,0), 1.0)
phase = cv2.resize(rng.random((H//6, W//6)).astype(np.float32), (W,H), interpolation=cv2.INTER_NEAREST)*2*np.pi
speed = cv2.resize(rng.integers(1,3,(H//6, W//6)).astype(np.float32), (W,H), interpolation=cv2.INTER_NEAREST)

# particles: river sparkles + rising energy motes toward the hands
P = []
for i in range(70):   # river sparkles drifting along the flow
    y0 = rng.uniform(520, 760); P.append(('river', rng.uniform(-200, W), y0, rng.random(), rng.integers(1,3), rng.uniform(1.2,2.6)))
for i in range(36):   # motes floating up around the hands / body
    hx = rng.choice([705, 1075, 870]); P.append(('rise', hx + rng.normal(0,55), rng.uniform(380,560), rng.random(), rng.integers(1,3), rng.uniform(1.0,2.2)))
cols = [(255,240,120),(255,170,230),(140,230,255),(255,255,255)]

ff = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
     '-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-preset','slow','-movflags','+faststart',OUT], stdin=subprocess.PIPE)
TAU = 2*np.pi
for f in range(N):
    th = TAU*f/N
    a2 = 2*th                                        # 4 s cycle for body motions
    dx = np.zeros((H,W), np.float32); dy = np.zeros((H,W), np.float32)
    # nebula drift (slow, low-frequency, background only)
    ndx = 3.5*np.sin(xx/170 + yy/230 + th) + 2.0*np.sin(yy/120 - xx/310 + 2*th + 1.3)
    ndy = 3.0*np.cos(xx/210 - yy/160 + th + 0.7) + 1.5*np.sin(xx/95 + 2*th)
    dx += ndx*free*(1-river); dy += ndy*free*(1-river)
    # river: travelling ripples that move rightward/up with the stream
    rw = river*free*(1-stones)
    dx += rw*(2.6*np.sin(xx/38 - yy/90 - 3*th) + 1.4*np.sin(xx/17 + yy/41 - 4*th))
    dy += rw*(1.8*np.sin(xx/52 + yy/30 - 3*th + 1.0) + 0.9*np.cos(xx/23 - 4*th))
    # cat float bob
    bob = 7.0*np.sin(a2)
    dy += cat*bob
    # arms: graceful raise/lower (rotation about shoulders), mirrored
    ang = np.deg2rad(11)*np.sin(a2 + 0.6)
    lx, ly = rot_field(800, 338+bob, ang, wL); dx += lx; dy += ly
    rx, ry = rot_field(945, 330+bob, -ang, wR); dx += rx; dy += ry
    # tail sway, lagging behind the arms
    tx, ty = rot_field(990, 490+bob, np.deg2rad(7)*np.sin(a2 - 1.2), wT); dx += tx; dy += ty
    frame = cv2.remap(src, xx-dx, yy-dy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # twinkle
    tw = np.sin(speed*th + phase)
    frame += (star*hi_w*np.where(tw>0, 1.6*tw, 0.85*tw))[...,None]
    # river shimmer: soft light bands travelling along stream
    band = (0.5+0.5*np.sin(xx/60 - yy/140 - 3*th))**6
    frame += (band*river*free*0.10)[...,None]*frame
    # eye / body glow pulse
    glow = np.exp(-(((xx-880)/240)**2 + ((yy-300-bob)/200)**2))*cat
    frame *= (1 + 0.06*(0.5+0.5*np.sin(a2+0.6))*glow)[...,None]
    # particles
    layer = np.zeros((H,W,3), np.float32)
    for k,(kind,x0,y0,off,n,sz) in enumerate(P):
        p = (n*f/N + off) % 1.0
        life = np.sin(np.pi*p)**1.5
        if kind == 'river':
            x = x0 + p*260; y = y0 - p*45 + 6*np.sin(TAU*p*2 + off*9)
        else:
            x = x0 + 12*np.sin(TAU*p + off*7); y = y0 - p*170 + cat[int(np.clip(y0,0,H-1)), int(np.clip(x0,0,W-1))]*bob
        c = cols[k % 4]
        cv2.circle(layer, (int(x*4), int(y*4)), int(sz*4), [ci*life for ci in c], -1, cv2.LINE_AA, 2)
    layer = cv2.GaussianBlur(layer, (0,0), 1.2) + cv2.GaussianBlur(layer, (0,0), 5)*1.5
    frame += layer
    ff.stdin.write(np.clip(frame,0,255).astype(np.uint8).tobytes())
    if f in (0, N//8, N//4, 3*N//8): cv2.imwrite(OUT.replace('.mp4', f'_f{f}.jpg'), np.clip(frame,0,255).astype(np.uint8))
ff.stdin.close(); ff.wait()

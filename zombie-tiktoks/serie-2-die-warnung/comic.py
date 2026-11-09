"""Comic-Zeichenbibliothek: Figuren, Räume und POV-Elemente mit dicken Konturen."""
import math, random
import cairo

INK = (0.07, 0.06, 0.07)
LW = 5.0          # Konturstärke in Weltkoordinaten
FONT = "Inter"


# ------------------------------------------------------------------ helpers
def C(c, a=1.0):
    if len(c) == 4:
        return c
    if max(c) > 1:
        return (c[0] / 255, c[1] / 255, c[2] / 255, a)
    return (c[0], c[1], c[2], a)


def mix(a, b, t):
    a, b = C(a), C(b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def dark(c, f=0.25):
    return mix(c, (0, 0, 0), f)


def fill_ink(ctx, color, lw=LW):
    ctx.set_source_rgba(*C(color))
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK, 1)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def poly(ctx, pts, color, lw=LW):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    fill_ink(ctx, color, lw)


def rect(ctx, x, y, w, h, color, lw=LW):
    ctx.rectangle(x, y, w, h)
    fill_ink(ctx, color, lw)


def rrect_path(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def rrect(ctx, x, y, w, h, r, color, lw=LW):
    rrect_path(ctx, x, y, w, h, r)
    fill_ink(ctx, color, lw)


def ell_path(ctx, cx, cy, rx, ry):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def ell(ctx, cx, cy, rx, ry, color, lw=LW):
    ell_path(ctx, cx, cy, rx, ry)
    fill_ink(ctx, color, lw)


def limb(ctx, pts, color, w, lw=LW):
    """Dicker Arm/Bein-Strich mit Kontur."""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for col, width in ((INK, w + 2 * lw), (C(color), w)):
        ctx.move_to(*pts[0])
        if len(pts) == 3:
            ctx.curve_to(pts[1][0], pts[1][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1])
        else:
            for p in pts[1:]:
                ctx.line_to(*p)
        ctx.set_source_rgba(*C(col))
        ctx.set_line_width(width)
        ctx.stroke()


def line(ctx, x1, y1, x2, y2, lw=LW, color=INK, a=1.0):
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.set_source_rgba(*(color if len(color) == 4 else (*C(color)[:3], a)))
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def font(ctx, size, bold=True):
    ctx.select_font_face(FONT + (" Black" if bold else ""), cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)


def text(ctx, s, x, y, size, color=(1, 1, 1), center=True, bold=True, outline=None, ow=6):
    font(ctx, size, bold)
    ext = ctx.text_extents(s)
    xx = x - ext.x_advance / 2 if center else x
    ctx.move_to(xx, y)
    if outline:
        ctx.text_path(s)
        ctx.set_source_rgba(*C(outline))
        ctx.set_line_width(ow)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*C(color))
        ctx.fill()
    else:
        ctx.set_source_rgba(*C(color))
        ctx.show_text(s)
    return ext.x_advance


# ------------------------------------------------------------------ figures
LOOKS = {
    "NOAH":  dict(skin=(240, 205, 175), hair=(160, 120, 60), hs="messy", glasses=True, top=(40, 55, 95), pants=(95, 100, 115)),
    "WOLFF": dict(skin=(232, 192, 160), hair=(150, 150, 150), hs="bald", beard=True, top=(170, 200, 230), vest=(120, 85, 55), pants=(70, 70, 80)),
    "LEA":   dict(skin=(250, 218, 195), hair=(205, 85, 40), hs="ponytail", top=(238, 238, 236), pants=(60, 70, 115), freckles=True),
    "SOMMER": dict(skin=(235, 200, 178), hair=(180, 180, 180), hs="bun", glasses=True, top=(40, 62, 105), shirt=(245, 242, 230), pants=(90, 90, 95)),
    "JONAS": dict(skin=(222, 182, 150), hair=(60, 45, 35), hs="buzz", top=(130, 130, 136), pants=(50, 55, 70)),
    "MAMA":  dict(skin=(240, 206, 180), hair=(115, 72, 40), hs="long", top=(205, 180, 135), coat=True, pants=(60, 55, 60)),
    "JANITOR": dict(skin=(225, 185, 155), hair=(90, 80, 70), hs="cap", top=(110, 118, 125), pants=(110, 118, 125), heavy=True),
    "SOLDAT": dict(skin=(225, 185, 155), hair=(80, 90, 55), hs="helmet", top=(95, 105, 65), pants=(85, 95, 60)),
}
STUDENT_TOPS = [(200, 60, 60), (60, 110, 170), (70, 140, 90), (230, 180, 60), (140, 90, 160), (230, 230, 230),
                (40, 40, 45), (220, 120, 50), (90, 160, 170)]
STUDENT_HAIR = [(40, 30, 25), (110, 70, 35), (200, 160, 80), (20, 20, 20), (150, 60, 30), (90, 60, 40)]
SKINS = [(245, 210, 180), (225, 180, 145), (180, 130, 95), (130, 90, 60), (240, 200, 170)]


def student_look(seed):
    r = random.Random(seed)
    return dict(skin=r.choice(SKINS), hair=r.choice(STUDENT_HAIR),
                hs=r.choice(["short", "short", "long", "ponytail", "messy", "buzz"]),
                glasses=r.random() < 0.2, top=r.choice(STUDENT_TOPS), pants=r.choice([(50, 55, 75), (70, 70, 80), (40, 45, 60)]),
                cap=r.random() < 0.1)


INF_SKIN = (165, 180, 150)


def person(ctx, L, x, y, s, view="front", pose="stand", t=0.0, talk=0.0, arms="down", expr="neutral",
           inf=0.0, seed=0.0, bandage=False, bite=False, walk=0.0, lean=0.0, look_dx=0.0):
    """Zeichnet eine Comic-Figur. (x, y) = Fußpunkt, s = Maßstab (1 ≈ 1000 px hoch)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    lw = LW / max(s, 0.15) * 0.9
    lw = min(lw, 14)
    skin = mix(L["skin"], INF_SKIN, inf) if inf else C(L["skin"])
    top = C(L["top"])
    pants = C(L.get("pants", (60, 60, 70)))
    heavy = 1.25 if L.get("heavy") else 1.0
    bob = math.sin(t * 2.0 + seed) * 4
    wph = t * 9 + seed
    ctx.rotate(lean + (math.sin(t * 1.3 + seed) * 0.05 if inf else 0))

    sit = pose in ("sit", "floor")
    if pose == "stand":
        hip, sh, hc = -450, -770, -880
    elif pose == "sit":        # auf Stuhl, von hinten/vorne
        hip, sh, hc = -420, -740, -850
    else:                      # auf dem Boden, Knie hoch
        hip, sh, hc = -230, -560, -670
    hc += bob
    sh += bob

    # legs
    if pose == "stand":
        sw = math.sin(wph) * 70 * walk
        for side, d in ((-1, sw), (1, -sw)):
            limb(ctx, [(side * 42 * heavy, hip), (side * 46 * heavy + d * 0.5, hip / 2), (side * 46 * heavy + d, -30)], pants, 78 * heavy, lw)
            ell(ctx, side * 50 * heavy + d + (0 if view == "back" else side * 6), -22, 50, 26, (35, 30, 30), lw)
    elif pose == "floor" and view == "front":
        for side in (-1, 1):
            limb(ctx, [(side * 50, hip), (side * 80, -330), (side * 70, -30)], pants, 82, lw)
            ell(ctx, side * 80, -330, 52, 46, pants, lw)
            ell(ctx, side * 72, -22, 52, 26, (35, 30, 30), lw)

    # long hair behind
    hs = L.get("hs", "short")
    hair = C(L["hair"])
    if hs == "long" and view == "front":
        poly(ctx, [(-95, hc - 40), (-110, hc + 170), (110, hc + 170), (95, hc - 40)], hair, lw)

    # back arm (drawn before torso)
    def arm(side, mode, front_layer):
        sx, sy = side * 108 * heavy, sh + 25
        if mode == "down":
            pts = [(sx, sy), (sx + side * 20, sy + 150), (sx + side * 12, sy + 300)]
        elif mode == "block":
            pts = [(sx, sy), (sx + side * 170, sy + 10), (sx + side * 330, sy - 10)]
        elif mode == "reach":
            k = math.sin(t * 3 + side + seed) * 15
            pts = [(sx, sy), (sx + side * 40, sy - 60 + k), (sx * 0.6 + side * 30, sy - 170 + k)]
        elif mode == "bang":
            if side > 0:
                k = abs(math.sin(t * 9 + seed)) * 40
                pts = [(sx, sy), (sx + 60, sy - 140), (sx + 40, sy - 300 - k)]
            else:
                pts = [(sx, sy), (sx - 20, sy + 150), (sx - 12, sy + 300)]
        elif mode == "hold_arm":
            pts = [(sx, sy), (sx + side * 10, sy + 170), (-side * 40, sy + 200)] if side > 0 else \
                  [(sx, sy), (sx - 20, sy + 150), (sx + 40, sy + 230)]
        elif mode == "knees":
            pts = [(sx, sy), (sx + side * 10, sy + 160), (side * 70, -310)]
        elif mode == "wave":
            if side > 0:
                k = math.sin(t * 7) * 40
                pts = [(sx, sy), (sx + 80, sy - 120), (sx + 70 + k, sy - 300)]
            else:
                pts = [(sx, sy), (sx - 20, sy + 150), (sx - 12, sy + 300)]
        elif mode == "pull":
            pts = [(sx, sy), (sx + 120, sy - 40), (sx + 260, sy - 120)] if side > 0 else \
                  [(sx, sy), (sx + 40, sy - 40), (sx + 180, sy - 120)]
        elif mode == "phone":
            pts = [(sx, sy), (sx + side * 10, sy + 170), (side * 30, sy + 140)]
        else:
            pts = [(sx, sy), (sx + side * 20, sy + 150), (sx + side * 12, sy + 300)]
        sleeve = top if not L.get("coat") else top
        limb(ctx, pts, sleeve, 66 * heavy, lw)
        hx, hy = pts[-1]
        if bite and side > 0 and mode in ("down", "hold_arm", "knees", "phone"):
            # hochgekrempelter Ärmel -> Unterarm sichtbar
            limb(ctx, [((pts[1][0] + hx) / 2, (pts[1][1] + hy) / 2), (hx, hy)], skin, 50, lw)
            mx, my = (pts[1][0] + hx * 3) / 4, (pts[1][1] + hy * 3) / 4
            ctx.set_source_rgba(0.45, 0.08, 0.1, 1)
            for k in range(5):
                a = k / 5 * 2 * math.pi
                ctx.arc(mx + math.cos(a) * 20, my + math.sin(a) * 12, 4.5, 0, 2 * math.pi)
                ctx.fill()
            ctx.set_source_rgba(0.3, 0.3, 0.45, 0.7)
            ctx.set_line_width(3)
            for k in range(3):
                ctx.move_to(mx, my); ctx.line_to(mx + 30 + k * 6, my - 40 + k * 25); ctx.stroke()
        if bandage and side > 0 and view == "front":
            mx, my = (pts[1][0] + hx) / 2, (pts[1][1] + hy) / 2
            ell(ctx, mx, my, 42, 34, (245, 245, 240), lw)
            ctx.set_source_rgba(0.55, 0.12, 0.12, 0.8)
            ell_path(ctx, mx + 6, my, 16, 12); ctx.fill()
        ell(ctx, hx, hy, 30, 30, skin, lw)
        if mode == "phone" and side > 0:
            rrect(ctx, hx - 28, hy - 70, 56, 95, 10, (25, 25, 30), lw)
            ctx.set_source_rgba(0.75, 0.85, 1, 0.9)
            ctx.rectangle(hx - 20, hy - 62, 40, 75); ctx.fill()

    if view == "front":
        arm(-1, arms if arms not in ("bang", "wave", "phone") else "down", False)

    # torso
    tw = 112 * heavy
    bottom = hip + (190 if L.get("coat") and pose == "stand" else 20)
    if view == "front" or view == "back":
        poly(ctx, [(-tw, sh + 10), (-tw + 8, sh - 12), (tw - 8, sh - 12), (tw, sh + 10),
                   (tw - 10, bottom), (-tw + 10, bottom)], top, lw)
    if view == "front":
        if L.get("vest"):
            poly(ctx, [(-tw + 10, sh + 10), (-30, sh + 10), (-10, bottom), (-tw + 18, bottom)], L["vest"], lw)
            poly(ctx, [(tw - 10, sh + 10), (30, sh + 10), (10, bottom), (tw - 18, bottom)], L["vest"], lw)
        if L.get("shirt"):
            poly(ctx, [(-35, sh - 10), (35, sh - 10), (20, sh + 200), (-20, sh + 200)], L["shirt"], lw)
        if L.get("coat"):
            line(ctx, 0, sh, 0, bottom, lw)
            for k in range(3):
                ell(ctx, 22, sh + 80 + k * 90, 9, 9, dark(top, 0.3), lw * 0.6)
        if hs != "helmet" and not L.get("vest") and not L.get("shirt") and not L.get("coat"):
            # Hoodie-Bändel + Tasche
            line(ctx, -22, sh, -26, sh + 110, lw * 0.8)
            line(ctx, 22, sh, 26, sh + 110, lw * 0.8)
            ctx.move_to(-70, bottom - 20); ctx.line_to(-55, bottom - 110); ctx.line_to(55, bottom - 110)
            ctx.line_to(70, bottom - 20)
            ctx.set_source_rgba(*INK, 1); ctx.set_line_width(lw * 0.7); ctx.stroke()
        if inf:
            ctx.set_source_rgba(0.35, 0.08, 0.08, 0.6 * inf)
            ell_path(ctx, -40, sh + 140, 28, 20); ctx.fill()
            ell_path(ctx, 50, sh + 230, 18, 26); ctx.fill()
    if view == "back" and hs == "hood":
        pass

    # neck
    rect(ctx, -26, sh - 45, 52, 40, dark(skin, 0.1), lw)

    # head
    ctx.save()
    ctx.translate(look_dx * 10, hc)
    if inf:
        ctx.rotate(math.sin(t * 1.1 + seed) * 0.12 + 0.1)
    ell(ctx, -80, 15, 16, 26, skin, lw)
    ell(ctx, 80, 15, 16, 26, skin, lw)
    ell(ctx, 0, 0, 80, 96, skin, lw)
    if view == "back":
        hair_back(ctx, L, lw)
    else:
        face(ctx, L, t, talk, expr, inf, seed, lw, look_dx)
    ctx.restore()

    if view == "front":
        arm(1, arms, True)
        if arms in ("bang", "wave", "phone"):
            arm(-1, "down", True) if False else None
    elif view == "back":
        a_mode = "down" if arms not in ("reach", "pull") else arms
        arm(-1, a_mode, True)
        arm(1, a_mode, True)
    ctx.restore()


def hair_back(ctx, L, lw):
    hs = L.get("hs", "short")
    hair = C(L["hair"])
    if hs in ("bald",):
        ctx.set_source_rgba(*hair)
        ell_path(ctx, 0, 30, 70, 50); ctx.fill()
        return
    if hs == "helmet":
        ell(ctx, 0, -25, 92, 80, hair, lw)
        return
    if hs == "cap":
        ell(ctx, 0, -20, 86, 70, hair, lw)
        return
    if hs == "buzz":
        ell(ctx, 0, -5, 80, 92, dark(hair, 0.0), lw)
        return
    ell(ctx, 0, -8, 86, 98, hair, lw)
    if hs == "long":
        poly(ctx, [(-86, 0), (-92, 170), (92, 170), (86, 0)], hair, lw)
    elif hs == "ponytail":
        limb(ctx, [(0, -40), (20, 60), (10, 170)], hair, 46, lw)
    elif hs == "bun":
        ell(ctx, 0, -95, 42, 38, hair, lw)
    elif hs == "messy":
        for k in range(5):
            ctx.move_to(-70 + k * 35, -80)
            ctx.line_to(-60 + k * 35, -112)
            ctx.line_to(-45 + k * 35, -82)
        ctx.set_source_rgba(*hair); ctx.fill()


def face(ctx, L, t, talk, expr, inf, seed, lw, look_dx=0):
    hs = L.get("hs", "short")
    hair = C(L["hair"])
    ex0 = look_dx * 8
    # hair front
    if hs in ("short", "messy", "ponytail", "long", "bun"):
        ctx.move_to(-84, -10)
        ctx.curve_to(-96, -110, 70, -140, 86, -20)
        ctx.curve_to(60, -60, 0, -70, -30, -50)
        ctx.curve_to(-55, -40, -70, -30, -84, -10)
        ctx.close_path()
        fill_ink(ctx, hair, lw)
        if hs == "messy":
            for k in range(4):
                ctx.move_to(-60 + k * 38, -78)
                ctx.line_to(-48 + k * 38, -118)
                ctx.line_to(-30 + k * 38, -84)
                ctx.close_path()
                fill_ink(ctx, hair, lw * 0.7)
        if hs == "bun":
            ell(ctx, 0, -112, 40, 34, hair, lw)
    elif hs == "bald":
        ctx.set_source_rgba(*hair)
        ell_path(ctx, -78, -10, 12, 40); ctx.fill()
        ell_path(ctx, 78, -10, 12, 40); ctx.fill()
    elif hs == "buzz":
        ctx.move_to(-82, -15)
        ctx.curve_to(-88, -110, 88, -110, 82, -15)
        ctx.curve_to(40, -55, -40, -55, -82, -15)
        ctx.close_path()
        fill_ink(ctx, dark(hair, 0.0), lw)
    elif hs == "cap":
        ctx.move_to(-86, -20)
        ctx.curve_to(-86, -120, 86, -120, 86, -20)
        ctx.close_path()
        fill_ink(ctx, hair, lw)
        ell(ctx, 30, -22, 75, 16, dark(hair, 0.2), lw)
    elif hs == "helmet":
        ctx.move_to(-95, -5)
        ctx.curve_to(-100, -135, 100, -135, 95, -5)
        ctx.close_path()
        fill_ink(ctx, hair, lw)

    if L.get("beard"):
        ctx.move_to(-72, 10)
        ctx.curve_to(-70, 120, 70, 120, 72, 10)
        ctx.curve_to(40, 45, -40, 45, -72, 10)
        ctx.close_path()
        fill_ink(ctx, hair, lw)

    # eyes
    blink = ((t + seed) % 3.9) < 0.12 and not inf
    for side in (-1, 1):
        ex, ey = side * 33 + ex0, -5
        if inf:
            ell(ctx, ex, ey, 17, 14, (235, 235, 215), lw * 0.7)
            ctx.set_source_rgba(0.25, 0.3, 0.25, 0.5)
            ell_path(ctx, ex, ey + 20, 18, 7); ctx.fill()
        elif blink:
            line(ctx, ex - 15, ey, ex + 15, ey, lw)
        else:
            big = expr in ("scared", "shock")
            ell(ctx, ex, ey, 15, 19 if big else 16, (255, 255, 255), lw * 0.7)
            ctx.set_source_rgba(*INK, 1)
            ctx.arc(ex + look_dx * 4, ey + 2, 7 if big else 8, 0, 2 * math.pi); ctx.fill()
        # brows
        by = ey - 34
        if expr in ("scared", "sad", "shock"):
            line(ctx, ex - 16, by + (6 if side > 0 else -4), ex + 16, by + (-4 if side > 0 else 6), lw * 1.1, dark(hair, 0.4))
        elif expr == "angry" or inf:
            line(ctx, ex - 16, by + (-6 if side > 0 else 8), ex + 16, by + (8 if side > 0 else -6), lw * 1.2, dark(hair, 0.4))
        else:
            line(ctx, ex - 16, by, ex + 16, by - 2, lw * 1.1, dark(hair, 0.4))
    if L.get("glasses"):
        ctx.set_source_rgba(*INK, 1)
        ctx.set_line_width(lw * 1.3)
        for side in (-1, 1):
            ctx.new_sub_path()
            ctx.arc(side * 33 + ex0, -5, 28, 0, 2 * math.pi)
        ctx.stroke()
        line(ctx, -5 + ex0, -8, 5 + ex0, -8, lw * 1.2)
    if L.get("freckles"):
        ctx.set_source_rgba(0.75, 0.45, 0.3, 0.8)
        for (fx, fy) in ((-40, 30), (-30, 36), (-48, 38), (40, 30), (30, 36), (48, 38)):
            ctx.arc(fx, fy, 3, 0, 2 * math.pi); ctx.fill()
    # nose
    ctx.move_to(4 + ex0, 10); ctx.curve_to(-6 + ex0, 30, 0 + ex0, 38, 10 + ex0, 36)
    ctx.set_source_rgba(*INK, 1); ctx.set_line_width(lw * 0.7); ctx.stroke()
    # mouth
    my = 60
    if inf:
        ell(ctx, 0, my, 26, 14 + talk * 14, (60, 15, 20), lw * 0.8)
        ctx.set_source_rgba(0.9, 0.88, 0.75, 1)
        for k in range(-2, 3):
            ctx.rectangle(k * 9 - 3, my - 12 - talk * 12, 6, 8); ctx.fill()
    elif talk > 0.05:
        ell(ctx, 0, my, 20 + talk * 5, 4 + talk * 20, (110, 30, 40), lw * 0.8)
    elif expr in ("scared", "shock"):
        ell(ctx, 0, my + 4, 10, 13, (110, 30, 40), lw * 0.8)
    elif expr == "smile":
        ctx.move_to(-24, my - 4); ctx.curve_to(-10, my + 14, 10, my + 14, 24, my - 4)
        ctx.set_source_rgba(*INK, 1); ctx.set_line_width(lw); ctx.stroke()
    elif expr == "sad":
        ctx.move_to(-20, my + 6); ctx.curve_to(-8, my - 4, 8, my - 4, 20, my + 6)
        ctx.set_source_rgba(*INK, 1); ctx.set_line_width(lw); ctx.stroke()
    else:
        line(ctx, -18, my, 18, my, lw)
    if inf:
        ctx.set_source_rgba(0.3, 0.25, 0.4, 0.6 * inf)
        ctx.set_line_width(3)
        for k in range(4):
            ctx.move_to(-60 + k * 8, 40 + k * 4); ctx.line_to(-75 + k * 10, 80 + k * 6); ctx.stroke()


# ------------------------------------------------------------------ rooms
def perspective_room(ctx, SW, SH, back, colors, ceiling_lines=True, seed=0):
    """back = (x0, y0, x1, y1) der Rückwand. colors: ceiling, wall, floor, left, right."""
    x0, y0, x1, y1 = back
    vx, vy = (x0 + x1) / 2, (y0 + y1) / 2
    big = 4000
    # ceiling
    poly(ctx, [(-big, -big), (SW + big, -big), (x1, y0), (x0, y0)], colors["ceiling"])
    if ceiling_lines:
        ctx.set_source_rgba(*INK, 0.35)
        ctx.set_line_width(3)
        for k in range(-12, 13):
            ctx.move_to(vx + (x1 - x0) * k / 12 * 0.5, y0)
            ctx.line_to(vx + k * 420, y0 - 2500)
            ctx.stroke()
    # floor
    poly(ctx, [(-big, SH + big), (SW + big, SH + big), (x1, y1), (x0, y1)], colors["floor"])
    ctx.set_source_rgba(*INK, 0.25)
    ctx.set_line_width(3)
    for k in range(-14, 15):
        ctx.move_to(vx + (x1 - x0) * k / 14 * 0.5, y1)
        ctx.line_to(vx + k * 480, y1 + 2500)
        ctx.stroke()
    for k in range(1, 12):
        f = (k / 12) ** 1.8
        yy = y1 + f * 1800
        ctx.move_to(-big, yy); ctx.line_to(SW + big, yy); ctx.stroke()
    # side walls
    poly(ctx, [(-big, -big), (x0, y0), (x0, y1), (-big, SH + big)], colors["left"])
    poly(ctx, [(SW + big, -big), (x1, y0), (x1, y1), (SW + big, SH + big)], colors["right"])
    rect(ctx, x0, y0, x1 - x0, y1 - y0, colors["wall"])


def side_point(back, side, depth, h):
    """Punkt auf Seitenwand: depth 0 = Rückwand, 1 = nah; h 0 = Boden, 1 = Decke."""
    x0, y0, x1, y1 = back
    wx = x0 if side < 0 else x1
    vx = (x0 + x1) / 2
    vy = (y0 + y1) / 2
    k = 1 + depth * 3.2
    px = vx + (wx - vx) * k
    py_floor = vy + (y1 - vy) * k
    py_ceil = vy + (y0 - vy) * k
    return px, py_floor + (py_ceil - py_floor) * h


def wall_quad(back, side, d0, d1, h0, h1):
    return [side_point(back, side, d0, h0), side_point(back, side, d1, h0),
            side_point(back, side, d1, h1), side_point(back, side, d0, h1)]


def floor_point(back, xf, depth):
    """xf -1..1 quer, depth 0 Rückwand .. 1 nah. Liefert (x, y, scale)."""
    x0, y0, x1, y1 = back
    vx, vy = (x0 + x1) / 2, (y0 + y1) / 2
    k = 1 + depth * 3.2
    x = vx + xf * (x1 - x0) / 2 * k
    y = vy + (y1 - vy) * k
    return x, y, k

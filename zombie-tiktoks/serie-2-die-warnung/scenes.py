"""Schauplätze der Serie. Jede Funktion zeichnet in Quell-Koordinaten (SW x SH)."""
import math, random
import cairo
from comic import *

SW, SH = 1300, 2300
CEIL = (222, 220, 212)
WALL = (238, 230, 210)
TEAL = (110, 165, 160)


def students_rows(ctx, back, t, P, talk, seed=1, rows=4, standing=0.0, front_student=True):
    r = random.Random(seed)
    seats = []
    for row in range(rows):
        d = 0.08 + row * 0.2
        for xf in (-0.78, -0.45, 0.45, 0.78):
            seats.append((d, xf, r.random() * 1000))
    seats.sort(key=lambda s: s[0])
    for (d, xf, sd) in seats:
        x, y, k = floor_point(back, xf, d)
        s = 0.2 * k
        stand = standing > (sd % 1)
        L = student_look(int(sd))
        # Tisch
        dw = 150 * s
        poly(ctx, [(x - dw, y - 400 * s), (x + dw, y - 400 * s), (x + dw * 1.1, y - 330 * s), (x - dw * 1.1, y - 330 * s)],
             (205, 165, 110), 3)
        if stand:
            person(ctx, L, x, y + 30 * s, s, view="back", pose="stand", t=t, seed=sd, look_dx=0)
        else:
            # Stuhl
            person(ctx, L, x, y, s, view="back", pose="sit", t=t, seed=sd)
            rrect(ctx, x - 115 * s, y - 640 * s, 230 * s, 200 * s, 18 * s, (60, 95, 150), 3)


def classroom(ctx, t, P, talk):
    view = P.get("view", "front")
    if view == "front":
        back = (250, 470, 1050, 1220)
        perspective_room(ctx, SW, SH, back, dict(ceiling=CEIL, wall=WALL, floor=(205, 200, 190), left=(232, 224, 205),
                                                   right=(235, 228, 208)))
        x0, y0, x1, y1 = back
        # Sockel-Streifen
        poly(ctx, [(x0, y1 - 110), (x1, y1 - 110), (x1, y1), (x0, y1)], TEAL)
        poly(ctx, wall_quad(back, -1, 0, 1.2, 0, 0.17), TEAL)
        poly(ctx, wall_quad(back, 1, 0, 1.2, 0, 0.17), TEAL)
        # Tafel
        rect(ctx, x0 + 70, y0 + 150, x1 - x0 - 140, 260, (45, 85, 65))
        ctx.set_source_rgba(0.95, 0.95, 0.9, 0.9)
        font(ctx, 30)
        ctx.move_to(x0 + 95, y0 + 200); ctx.show_text(P.get("board", "Mathe-Klausur"))
        font(ctx, 22, bold=False)
        for i, ln in enumerate(P.get("board2", ["• Lineare Funktionen", "• Steigung m = Δy / Δx"])):
            ctx.move_to(x0 + 95, y0 + 245 + i * 34); ctx.show_text(ln)
        font(ctx, 24)
        ctx.move_to(x1 - 210, y0 + 200); ctx.show_text("14.11.")
        # Uhr + Lautsprecher
        ell(ctx, x0 + 40, y0 + 80, 30, 30, (250, 250, 245), 4)
        line(ctx, x0 + 40, y0 + 80, x0 + 40, y0 + 60, 4); line(ctx, x0 + 40, y0 + 80, x0 + 55, y0 + 85, 4)
        rrect(ctx, x1 - 120, y0 + 30, 80, 60, 8, (90, 90, 95), 4)
        for k in range(3):
            line(ctx, x1 - 105, y0 + 48 + k * 13, x1 - 55, y0 + 48 + k * 13, 3)
        # Fenster links
        for i in range(3):
            q = wall_quad(back, -1, 0.06 + i * 0.32, 0.32 + i * 0.32, 0.3, 0.85)
            poly(ctx, q, (150, 200, 230))
            ctx.save(); ctx.move_to(*q[0]); [ctx.line_to(*p) for p in q[1:]]; ctx.close_path(); ctx.clip()
            ctx.set_source_rgba(0.55, 0.6, 0.62, 1)
            cx = (q[0][0] + q[1][0]) / 2
            ctx.rectangle(cx - 60, q[0][1] - 260, 120, 260); ctx.fill()
            ctx.set_source_rgba(0.35, 0.6, 0.35, 1)
            ell_path(ctx, cx + 40, q[0][1] - 60, 90, 70); ctx.fill()
            ctx.restore()
            mx = [(q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2]
            mt = [(q[3][0] + q[2][0]) / 2, (q[3][1] + q[2][1]) / 2]
            line(ctx, mx[0], mx[1], mt[0], mt[1], 6)
        # Tür rechts
        q = wall_quad(back, 1, 0.12, 0.42, 0, 0.62)
        poly(ctx, q, (140, 90, 55))
        # Poster
        poly(ctx, wall_quad(back, 1, 0.55, 0.75, 0.45, 0.75), (240, 240, 235))
        # Deckenlampen
        for d in (0.2, 0.6, 1.1):
            x, y, k = floor_point(back, 0, d)
            yy = (y0 - (y1 - y0) / 2 * (k - 1)) + 20 * k
            rrect(ctx, (x0 + x1) / 2 - 120 * k, yy, 240 * k, 26 * k, 6, (250, 250, 245) if P.get("lights", True) else (170, 170, 165), 4)
        # Lehrer
        if P.get("teacher", True):
            tx = P.get("teacher_x", 0.0)
            td = P.get("teacher_d", 0.05)
            x, y, k = floor_point(back, tx, td)
            person(ctx, LOOKS["WOLFF"], x, y, 0.2 * k, view="front", t=t, talk=talk.get("WOLFF", 0),
                   expr=P.get("teacher_expr", "neutral"), arms=P.get("teacher_arms", "down"), walk=P.get("teacher_walk", 0))
        students_rows(ctx, back, t, P, talk, standing=P.get("standing", 0.0))
        # Lea vorne rechts (umgedreht)
        if P.get("lea", True):
            x, y, k = floor_point(back, 0.62, 0.92)
            person(ctx, LOOKS["LEA"], x + 60, y + 40, 0.19 * k, view="front", pose="sit", t=t, talk=talk.get("LEA", 0),
                   expr=P.get("lea_expr", "scared"), arms=P.get("lea_arms", "phone"), look_dx=-1)
            rrect(ctx, x + 60 - 115 * 0.19 * k, y + 40 - 440 * 0.19 * k, 230 * 0.19 * k, 160 * 0.19 * k, 10, (60, 95, 150), 4)
        # Schüler direkt vor dir
        if P.get("front_student", True):
            person(ctx, student_look(77), 650, 2230, 0.95, view="back", pose="sit", t=t, seed=3)
            rrect(ctx, 650 - 130, 2230 - 640 * 0.95, 260, 230, 22, (60, 95, 150), 6)
        if P.get("dark", 0):
            ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"]); ctx.paint()
    elif view == "window":
        # Blick aus dem Fenster auf den Schulhof
        g = cairo.LinearGradient(0, 0, 0, 1300)
        g.add_color_stop_rgb(0, 0.55, 0.75, 0.92); g.add_color_stop_rgb(1, 0.85, 0.9, 0.95)
        ctx.set_source(g); ctx.rectangle(-500, -500, SW + 1000, SH + 1000); ctx.fill()
        for i, (bx, bw, bh) in enumerate(((-100, 350, 520), (280, 300, 380), (620, 420, 600), (1060, 400, 450))):
            rect(ctx, bx, 1150 - bh, bw, bh, (175, 170, 165))
            for wy in range(1150 - bh + 40, 1120, 70):
                for wx in range(bx + 30, bx + bw - 40, 70):
                    rect(ctx, wx, wy, 34, 40, (120, 150, 175), 3)
        for tx in (150, 900):
            ell(ctx, tx, 1050, 150, 120, (90, 150, 80))
            rect(ctx, tx - 15, 1100, 30, 120, (110, 80, 50), 4)
        poly(ctx, [(-500, 1150), (SW + 500, 1150), (SW + 500, SH + 500), (-500, SH + 500)], (170, 168, 160))
        # Fahrradständer
        for k in range(6):
            ctx.set_source_rgba(*INK, 1); ctx.set_line_width(5)
            ctx.arc(150 + k * 70, 1330, 30, math.pi, 2 * math.pi); ctx.stroke()
        # Hausmeister und Schüler
        st = P.get("yard", "walk")
        jx = P.get("jan_x", 700)
        person(ctx, LOOKS["JANITOR"], jx, 1560, 0.42, view="front", t=t, inf=1.0, arms="reach", walk=1 if st == "walk" else 0)
        if st in ("walk", "bite"):
            sx = P.get("stu_x", 520)
            person(ctx, student_look(5), sx, 1570, 0.38, view="front", t=t, expr="scared",
                   lean=-0.25 if st == "bite" else 0)
        if st == "chaos":
            for k in range(6):
                rx = (k * 230 + t * 260 * (1 if k % 2 else -1)) % 1600 - 150
                person(ctx, student_look(20 + k), rx, 1470 + (k % 3) * 40, 0.24, view="back" if k % 2 else "front",
                       t=t, walk=1, expr="scared", seed=k)
            person(ctx, student_look(5), 760, 1430, 0.26, view="front", t=t, inf=0.8, arms="reach", seed=9)
        # Fensterrahmen innen
        ctx.set_source_rgba(*C((90, 95, 100)))
        ctx.rectangle(-500, -500, SW + 1000, 380); ctx.fill()
        ctx.rectangle(-500, 1720, SW + 1000, 1500); ctx.fill()
        rect(ctx, -500, 1700, SW + 1000, 40, (200, 200, 195))
        for fx in (-30, 640, 1310):
            rect(ctx, fx - 22, -500, 44, SH + 1000, (225, 225, 220))
        rect(ctx, -500, 860, SW + 1000, 30, (225, 225, 220))
        poly(ctx, [(-500, 1740), (SW + 500, 1740), (SW + 500, SH + 500), (-500, SH + 500)], TEAL)
        # Schüler am Fenster (von hinten)
        if P.get("crowd", False):
            for k, x in enumerate((180, 470, 820, 1130)):
                person(ctx, student_look(40 + k), x, 2450, 0.9, view="back", t=t, seed=k)
    elif view == "door":
        back = (100, 300, 1200, 1500)
        rect(ctx, -500, -500, SW + 1000, SH + 1000, WALL)
        rect(ctx, -500, 1500, SW + 1000, 1500, (205, 200, 190))
        rect(ctx, -500, 1340, SW + 1000, 160, TEAL)
        # Tür
        op = P.get("door_open", 0.0)
        rect(ctx, 330, 300, 640, 1200, (60, 55, 50))   # Türöffnung
        if op > 0:
            # Flur sichtbar
            rect(ctx, 340, 310, 620, 1190, (200, 195, 180))
            for k in range(3):
                person(ctx, LOOKS["JANITOR"], 520 + k * 120, 1300, 0.22, t=t, inf=1, arms="reach", seed=k)
        ctx.save()
        ctx.translate(330, 300)
        ctx.scale(1 - op * 0.85, 1)
        rect(ctx, 0, 0, 640, 1200, (150, 98, 60))
        # Glasfenster
        rect(ctx, 380, 140, 170, 420, (170, 200, 215))
        ctx.restore()
        if op == 0:
            ctx.save()
            ctx.rectangle(330 + 380, 300 + 140, 170, 420); ctx.clip()
            if P.get("noah_glass", False):
                ctx.set_source_rgba(0.55, 0.55, 0.52, 1); ctx.paint()
                person(ctx, LOOKS["NOAH"], 790, 1420, 1.0, t=t, talk=talk.get("NOAH", 0), expr="scared", arms="bang")
                if P.get("glass_grey", False):
                    person(ctx, LOOKS["JANITOR"], 860, 1500, 0.9, t=t, inf=1, arms="reach")
            ctx.restore()
            rect(ctx, 330 + 380, 300 + 140, 170, 420, (0, 0, 0, 0), 8)
            ell(ctx, 360, 900, 30, 30, (200, 190, 140))
            rect(ctx, 350, 880, 110, 30, (200, 190, 140), 5)
        if op > 0 and P.get("noah_in", False):
            person(ctx, LOOKS["NOAH"], 620, 2000, 1.15, t=t, talk=talk.get("NOAH", 0), expr="scared", lean=0.15,
                   arms="hold_arm")
        # Barrikade
        if P.get("tables", 0) > 0:
            n = int(P["tables"] * 3 + 0.5)
            for k in range(n):
                poly(ctx, [(250 + k * 60, 1700 - k * 150), (1050 + k * 30, 1700 - k * 150), (1080 + k * 30, 1760 - k * 150),
                           (230 + k * 60, 1760 - k * 150)], (205, 165, 110))
                rect(ctx, 280 + k * 60, 1760 - k * 150, 26, 200, (120, 120, 125), 4)
                rect(ctx, 1020 + k * 30, 1760 - k * 150, 26, 200, (120, 120, 125), 4)
        # Lehrer davor
        if P.get("teacher", False):
            person(ctx, LOOKS["WOLFF"], P.get("teacher_x", 650), 2300, 1.25, t=t, talk=talk.get("WOLFF", 0),
                   expr=P.get("teacher_expr", "angry"), arms=P.get("teacher_arms", "block"))
        if P.get("dark", 0):
            ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"]); ctx.paint()
    elif view == "floor":
        rect(ctx, -500, -500, SW + 1000, SH + 1000, WALL)
        rect(ctx, -500, 1150, SW + 1000, 180, TEAL)
        rect(ctx, -500, 1330, SW + 1000, 2000, (205, 200, 190))
        # Poster
        rrect(ctx, 120, 420, 260, 340, 6, (245, 240, 230))
        text(ctx, "MATHE", 250, 500, 40, (0.2, 0.2, 0.2))
        text(ctx, "y = mx + b", 250, 580, 34, (0.2, 0.4, 0.7))
        person(ctx, LOOKS["NOAH"], 650, 2050, 1.35, pose="floor", t=t, talk=talk.get("NOAH", 0),
               expr=P.get("noah_expr", "scared"), arms="knees" if not P.get("bite") else "hold_arm",
               bite=P.get("bite", False), inf=P.get("noah_inf", 0.0))
        if P.get("teacher_hand", False):
            limb(ctx, [(1500, 1100), (1150, 1250), (900, 1420)], (170, 200, 230), 110)
            ell(ctx, 900, 1420, 55, 50, LOOKS["WOLFF"]["skin"])
        if P.get("dark", 0):
            ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"]); ctx.paint()


def hallway(ctx, t, P, talk):
    back = (500, 820, 800, 1180)
    fl = P.get("flicker", 0)
    perspective_room(ctx, SW, SH, back, dict(ceiling=CEIL, wall=(140, 90, 60), floor=(200, 196, 186),
                                               left=(235, 228, 210), right=(235, 228, 210)))
    # Fenster links
    for i in range(5):
        d0 = 0.05 + i * 0.25
        poly(ctx, wall_quad(back, -1, d0, d0 + 0.18, 0.35, 0.85), (165, 205, 225))
    poly(ctx, wall_quad(back, -1, 0, 1.6, 0, 0.3), (190, 120, 90))
    # Spinde rechts
    for i in range(14):
        d0 = 0.0 + i * 0.1
        poly(ctx, wall_quad(back, 1, d0, d0 + 0.1, 0.0, 0.62), (70, 150, 140), 4)
        a = wall_quad(back, 1, d0 + 0.02, d0 + 0.08, 0.45, 0.5)
        poly(ctx, a, (40, 90, 85), 2)
    # Lampen
    for d in (0.1, 0.3, 0.55, 0.85, 1.2):
        x, y, k = floor_point(back, 0, d)
        vy = (back[1] + back[3]) / 2
        yy = vy + (back[1] - vy) * k
        on = not (fl and (math.sin(t * 23 + d * 7) > 0.6))
        poly(ctx, [(x - 40 * k, yy + 4 * k), (x + 40 * k, yy + 4 * k), (x + 46 * k, yy + 26 * k), (x - 46 * k, yy + 26 * k)],
             (250, 250, 240) if on else (150, 150, 145), 4)
    # Schild
    sx, sy, sk = floor_point(back, 0, 0.55)
    yy = (back[1] + back[3]) / 2 - ((back[3] - back[1]) / 2) * sk + 120
    rrect(ctx, sx - 140, yy, 280, 90, 8, (200, 40, 40))
    text(ctx, "SCHUTZRAUM", sx, yy + 45, 34, (1, 1, 1))
    text(ctx, "KELLER  →", sx, yy + 78, 22, (1, 1, 1), bold=False)
    # Zettel
    r = random.Random(4)
    for _ in range(30):
        d = r.random() * 1.4
        x, y, k = floor_point(back, r.uniform(-0.9, 0.9), d)
        ctx.save(); ctx.translate(x, y); ctx.rotate(r.uniform(-1, 1)); ctx.scale(k, k * 0.5)
        rect(ctx, -18, -14, 36, 28, r.choice([(245, 245, 240), (240, 220, 140), (200, 220, 245)]), 2)
        ctx.restore()
    if P.get("bags", False):
        for (xf, d, c) in ((-0.5, 0.9, (200, 70, 80)), (0.3, 1.2, (90, 90, 160))):
            x, y, k = floor_point(back, xf, d)
            rrect(ctx, x - 40 * k, y - 60 * k, 80 * k, 60 * k, 12 * k, c, 4)
        x, y, k = floor_point(back, 0.1, 1.05)
        rrect(ctx, x - 20 * k, y - 12 * k, 40 * k, 24 * k, 4, (20, 20, 25), 3)
        ctx.set_source_rgba(0.6, 0.85, 1, 0.9 if math.sin(t * 4) > 0 else 0.4)
        ctx.rectangle(x - 15 * k, y - 8 * k, 30 * k, 16 * k); ctx.fill()
    # Figuren am Ende
    n = P.get("figures", 0)
    turned = P.get("turned", 0.0)
    for i in range(n):
        xf = -0.6 + i * 1.2 / max(n - 1, 1)
        d = P.get("fig_d", 0.05) + (i % 2) * 0.05
        x, y, k = floor_point(back, xf, d)
        person(ctx, student_look(60 + i) if i % 2 else LOOKS["JANITOR"], x, y, 0.13 * k,
               view="front" if turned > i / n else "back", t=t, inf=1.0, arms="reach" if turned > i / n else "down", seed=i)
    # Begleiter vor dir
    for key, xf, d in (("NOAH", -0.25, P.get("noah_d", -1)), ("LEA", 0.3, P.get("lea_d", -1))):
        if d >= 0:
            x, y, k = floor_point(back, xf, d)
            person(ctx, LOOKS[key], x, y, 0.2 * k, view=P.get("comp_view", "back"), t=t, talk=talk.get(key, 0),
                   walk=P.get("walk", 0), expr="scared")
    if P.get("dark", 0):
        ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"] * (1.3 if fl and math.sin(t * 23) > 0.6 else 1)); ctx.paint()


def stairs(ctx, t, P, talk):
    rect(ctx, -500, -500, SW + 1000, SH + 1000, (225, 218, 200))
    # Treppenstufen nach unten
    for i in range(12):
        f = i / 12
        y = 1000 + f ** 1.3 * 1500
        w = 300 + f * 900
        poly(ctx, [(650 - w, y), (650 + w, y), (650 + w * 1.08, y + 60 + f * 90), (650 - w * 1.08, y + 60 + f * 90)],
             (185, 180, 170) if i % 2 else (200, 195, 185), 4)
    poly(ctx, [(-500, -500), (350, 700), (350, 1000), (-500, 2800)], (215, 205, 185))
    poly(ctx, [(SW + 500, -500), (950, 700), (950, 1000), (SW + 500, 2800)], (215, 205, 185))
    rect(ctx, 350, 700, 600, 300, (150, 155, 150))
    # Geländer
    limb(ctx, [(-200, 900), (200, 1300), (500, 1050)], (200, 40, 40), 22)
    rrect(ctx, 470, 760, 360, 110, 10, (200, 40, 40))
    text(ctx, "SCHUTZRAUM", 650, 812, 40, (1, 1, 1))
    text(ctx, "TREPPE  ↓", 650, 852, 26, (1, 1, 1), bold=False)
    for key, xf, d in (("NOAH", -0.2, P.get("noah_d", -1)), ("LEA", 0.25, P.get("lea_d", -1))):
        if d >= 0:
            person(ctx, LOOKS[key], 650 + xf * 700, 1300 + d * 700, 0.45 + d * 0.4, view="back", t=t, walk=1)
    if P.get("dark", 0):
        ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"]); ctx.paint()


def steeldoor(ctx, t, P, talk):
    rect(ctx, -500, -500, SW + 1000, SH + 1000, (150, 150, 145))
    for k in range(-3, 10):
        line(ctx, -500, 200 + k * 260, SW + 500, 200 + k * 260, 3, INK, 0.3)
    rect(ctx, -500, 1700, SW + 1000, 1500, (110, 110, 108))
    rect(ctx, 230, 380, 840, 1330, (60, 65, 60))
    op = P.get("open", 0.3)
    # Spalt: dahinter Licht + Frau Sommer
    gap = 840 * op
    ctx.save(); ctx.rectangle(230, 380, gap, 1330); ctx.clip()
    rect(ctx, 230, 380, 840, 1330, (235, 225, 190))
    if P.get("sommer", True):
        person(ctx, LOOKS["SOMMER"], 230 + gap / 2 + 60, 2100, 1.35, t=t, talk=talk.get("SOMMER", 0), expr="scared", arms="pull")
    ctx.restore()
    ctx.save()
    ctx.translate(230 + gap, 380)
    rect(ctx, 0, 0, 840 - gap, 1330, (60, 115, 95))
    for yy in (60, 1270):
        for xx in range(30, int(840 - gap) - 10, 60):
            ell(ctx, xx, yy, 7, 7, (40, 80, 65), 2)
    ell(ctx, 120, 665, 70, 70, (40, 80, 65), 8)
    ctx.restore()
    rrect(ctx, 480, 240, 340, 100, 10, (200, 40, 40))
    text(ctx, "SCHUTZRAUM", 650, 305, 46, (1, 1, 1))
    if P.get("hand", False):
        limb(ctx, [(1500, 1900), (1300, 1700), (1150 + math.sin(t * 6) * 30, 1550)], (130, 150, 130), 90)
        ell(ctx, 1150 + math.sin(t * 6) * 30, 1550, 50, 45, INF_SKIN)


def shelter(ctx, t, P, talk):
    view = P.get("view", "wide")
    # Grundraum
    rect(ctx, -500, -500, SW + 1000, SH + 1000, (150, 150, 145))
    ctx.set_source_rgba(*C((120, 122, 120)))
    ell_path(ctx, 650, 200, 1400, 700); ctx.fill()
    for k in range(3):
        ctx.set_source_rgba(*C((220, 170, 40)))
        ctx.set_line_width(26)
        ctx.arc(650, 1600 + k * 40, 1500 + k * 60, math.pi * 1.15, math.pi * 1.85)
        ctx.stroke()
    rect(ctx, -500, 1150, SW + 1000, 2000, (120, 120, 118))
    line(ctx, -500, 1150, SW + 500, 1150, 5)
    # Rückwand-Elemente
    for x in (120, 1130):
        rect(ctx, x - 50, 600, 100, 560, (170, 170, 165))
    rect(ctx, 520, 760, 260, 390, (60, 115, 95))                 # Ausgangstür
    rrect(ctx, 560, 700, 180, 50, 6, (40, 150, 70))
    text(ctx, "AUSGANG", 650, 735, 28, (1, 1, 1))
    rrect(ctx, 230, 800, 220, 80, 6, (200, 40, 40))
    text(ctx, "SCHUTZRAUM", 340, 852, 30, (1, 1, 1))
    for sx in (880,):
        rect(ctx, sx, 820, 200, 330, (90, 90, 95))
        for k in range(4):
            line(ctx, sx, 900 + k * 80, sx + 200, 900 + k * 80, 5)
            for b in range(5):
                rrect(ctx, sx + 12 + b * 37, 860 + k * 80, 26, 38, 6, (150, 200, 230), 2)
    # Schüler an den Wänden
    r = random.Random(8)
    for i in range(16):
        side = -1 if i % 2 else 1
        d = (i // 2) / 8
        x = 650 + side * (250 + d * 700)
        y = 1170 + d * 600
        if abs(x - 650) < 200:
            continue
        L = student_look(100 + i)
        if P.get("empty", False):
            continue
        person(ctx, L, x, y, 0.2 + d * 0.25, pose="floor", t=t, expr="scared", arms="knees", seed=i,
               inf=(1.0 if P.get("infected_one") and i == 5 else 0))
    # Frau Sommer
    if P.get("sommer", True):
        sx = P.get("sommer_x", 650)
        sd = P.get("sommer_s", 0.32)
        person(ctx, LOOKS["SOMMER"], sx, 1200 + (sd - 0.32) * 900, sd, t=t, talk=talk.get("SOMMER", 0),
               expr=P.get("sommer_expr", "angry"), arms=P.get("sommer_arms", "down"))
    if P.get("jonas", False):
        inf = P.get("jonas_inf", 0)
        js = P.get("jonas_s", 0.5)
        person(ctx, LOOKS["JONAS"], P.get("jonas_x", 1050), 1450 + (js - 0.5) * 900, js,
               pose=P.get("jonas_pose", "floor"), t=t, talk=talk.get("JONAS", 0), expr="angry",
               arms="reach" if inf else "hold_arm", inf=inf)
    if P.get("noah", False):
        person(ctx, LOOKS["NOAH"], P.get("noah_x", 230), 2350, P.get("noah_s", 1.0), pose="floor", t=t,
               talk=talk.get("NOAH", 0), expr=P.get("noah_expr", "sad"), arms="hold_arm", bite=P.get("noah_bite", False))
    if P.get("lea", False):
        person(ctx, LOOKS["LEA"], P.get("lea_x", 1100), 2350, 0.95, pose="floor", t=t, talk=talk.get("LEA", 0),
               expr="scared", arms="knees")
    # Lampen
    on = P.get("lights", 1.0)
    for x in (300, 650, 1000):
        line(ctx, x, 380, x, 460, 4)
        ell(ctx, x, 470, 22, 16, (255, 245, 200) if on > 0.5 else (90, 90, 85), 4)
    if P.get("dark", 0):
        d = P["dark"]
        fx = P.get("flash_x", None)
        if fx is None:
            ctx.set_source_rgba(0.01, 0.01, 0.02, d); ctx.paint()
        else:
            fy = P.get("flash_y", 1250)
            g = cairo.RadialGradient(fx, fy, 60, fx, fy, 520)
            g.add_color_stop_rgba(0, 0.02, 0.02, 0.03, 0.0)
            g.add_color_stop_rgba(0.7, 0.02, 0.02, 0.03, d * 0.75)
            g.add_color_stop_rgba(1, 0.01, 0.01, 0.02, d)
            ctx.set_source(g); ctx.rectangle(-500, -500, SW + 1000, SH + 1000); ctx.fill()


def yard(ctx, t, P, talk):
    g = cairo.LinearGradient(0, 0, 0, 1100)
    g.add_color_stop_rgb(0, 0.5, 0.72, 0.92); g.add_color_stop_rgb(1, 0.82, 0.88, 0.94)
    ctx.set_source(g); ctx.rectangle(-500, -500, SW + 1000, SH + 1000); ctx.fill()
    for (cx, cy, rr) in ((250, 300, 90), (380, 280, 70), (950, 380, 80), (1050, 360, 60)):
        ctx.set_source_rgba(1, 1, 1, 0.95); ell_path(ctx, cx, cy, rr * 1.5, rr * 0.7); ctx.fill()
    # Rauch
    for k in range(8):
        ctx.set_source_rgba(0.35, 0.35, 0.38, 0.5)
        ell_path(ctx, 1150 + k * 20, 900 - k * 70, 70 + k * 12, 60 + k * 10); ctx.fill()
    # Schulgebäude
    rect(ctx, -300, 620, 1050, 520, (200, 190, 175))
    for wy in (680, 820, 960):
        for wx in range(-260, 720, 110):
            rect(ctx, wx, wy, 70, 90, (140, 175, 200), 4)
    rect(ctx, 820, 760, 700, 380, (175, 160, 140))
    rrect(ctx, 900, 800, 380, 80, 6, (240, 240, 235))
    text(ctx, "TURNHALLE", 1090, 855, 42, (0.15, 0.25, 0.5))
    rect(ctx, 1010, 950, 170, 190, (90, 95, 105))
    poly(ctx, [(-500, 1140), (SW + 500, 1140), (SW + 500, SH + 500), (-500, SH + 500)], (165, 165, 160))
    for k in range(10):
        line(ctx, -500, 1180 + k * k * 14, SW + 500, 1180 + k * k * 14, 3, INK, 0.2)
    # Fahrradständer
    if P.get("bikes", True):
        for k in range(7):
            ctx.set_source_rgba(*INK, 1); ctx.set_line_width(7)
            ctx.arc(150 + k * 120, 1500, 55, math.pi, 2 * math.pi); ctx.stroke()
    # Auto
    if P.get("car", True):
        cx = P.get("car_x", 350)
        rrect(ctx, cx - 330, 1180, 660, 200, 40, (190, 195, 200))
        poly(ctx, [(cx - 220, 1180), (cx - 140, 1060), (cx + 150, 1060), (cx + 230, 1180)], (190, 195, 200))
        poly(ctx, [(cx - 190, 1175), (cx - 125, 1080), (cx, 1080), (cx, 1175)], (150, 190, 215))
        poly(ctx, [(cx + 20, 1175), (cx + 20, 1080), (cx + 140, 1080), (cx + 200, 1175)], (150, 190, 215))
        if P.get("car_open", True):
            poly(ctx, [(cx - 200, 1180), (cx - 360, 1120), (cx - 360, 1330), (cx - 200, 1360)], (170, 175, 180))
        for wx in (cx - 210, cx + 210):
            ell(ctx, wx, 1380, 70, 70, (35, 35, 38)); ell(ctx, wx, 1380, 30, 30, (150, 150, 155))
        blink = (t % 1.0) < 0.5
        ell(ctx, cx + 320, 1240, 18, 14, (255, 170, 30) if blink else (150, 110, 60), 3)
        ell(ctx, cx - 320, 1240, 18, 14, (255, 170, 30) if blink else (150, 110, 60), 3)
    # Infizierte
    for k in range(P.get("infected", 3)):
        x = (300 + k * 380 + t * 18 * (1 if k % 2 else -1)) % 1500 - 100
        person(ctx, student_look(200 + k) if k % 2 else LOOKS["JANITOR"], x, 1250 + (k % 3) * 25, 0.18, t=t, inf=1,
               arms="reach", walk=0.6, seed=k)
    if P.get("close_inf", False):
        person(ctx, student_look(301), P.get("close_x", 900), 2250, 1.0, t=t, inf=1, arms="reach", walk=0.5, seed=4)
        for k in range(4):
            ctx.set_source_rgba(*INK, 1); ctx.set_line_width(22)
            ctx.arc(150 + k * 360, 2600, 330, math.pi * 1.1, math.pi * 1.9); ctx.stroke()
    for key, x, s in (("NOAH", P.get("noah_x", -1), P.get("noah_s", 0.9)), ("LEA", P.get("lea_x", -1), 0.9)):
        if x >= 0:
            person(ctx, LOOKS[key], x, 2300, s, t=t, talk=talk.get(key, 0), expr="scared",
                   arms="hold_arm" if key == "NOAH" else "down", inf=P.get("noah_inf", 0) if key == "NOAH" else 0,
                   view=P.get("comp_view", "front"), walk=P.get("walk", 0))


def car_inside(ctx, t, P, talk):
    rect(ctx, -500, -500, SW + 1000, SH + 1000, (60, 62, 68))
    poly(ctx, [(100, 300), (1200, 300), (1300, 900), (0, 900)], (160, 195, 220))
    rect(ctx, 400, 450, 500, 300, (190, 185, 175))
    poly(ctx, [(-500, 900), (SW + 500, 900), (SW + 500, 1250), (-500, 1250)], (45, 45, 50))
    ctx.set_source_rgba(*INK, 1); ctx.set_line_width(40)
    ctx.arc(350, 1350, 230, math.pi * 1.05, math.pi * 1.95); ctx.stroke()
    ctx.set_source_rgba(*C((60, 60, 66))); ctx.set_line_width(30)
    ctx.arc(350, 1350, 230, math.pi * 1.05, math.pi * 1.95); ctx.stroke()
    rrect(ctx, 150, 1300, 450, 1100, 80, (120, 85, 60))
    rrect(ctx, 200, 1000, 350, 380, 60, (130, 92, 65))
    rrect(ctx, 750, 1300, 450, 1100, 80, (120, 85, 60))
    rrect(ctx, 800, 1000, 350, 380, 60, (130, 92, 65))
    rrect(ctx, 830, 1500, 300, 240, 40, (170, 40, 60))
    limb(ctx, [(880, 1510), (980, 1400), (1080, 1510)], (90, 30, 40), 18)
    blink = (t % 1.0) < 0.5
    poly(ctx, [(650, 1060), (690, 1120), (610, 1120)], (240, 60, 40) if blink else (90, 40, 30), 3)


def gym(ctx, t, P, talk):
    back = (250, 500, 1050, 1150)
    perspective_room(ctx, SW, SH, back, dict(ceiling=(200, 200, 205), wall=(210, 205, 190), floor=(205, 165, 105),
                                               left=(225, 220, 205), right=(225, 220, 205)), ceiling_lines=False)
    ctx.set_source_rgba(0.85, 0.25, 0.2, 0.9); ctx.set_line_width(8)
    ell_path(ctx, 650, 1500, 420, 140); ctx.stroke()
    line(ctx, -500, 1500, SW + 500, 1500, 8, (0.85, 0.25, 0.2), 0.9)
    rect(ctx, 560, 640, 180, 120, (245, 245, 245))
    ell(ctx, 650, 790, 50, 14, (230, 110, 40), 5)
    for i, x in enumerate((330, 520, 780, 960)):
        rrect(ctx, x - 90, 1200, 180, 70, 10, (60, 100, 170), 4)
        person(ctx, student_look(400 + i), x, 1225, 0.22, pose="floor", t=t, expr="sad", arms="knees", seed=i)
    rrect(ctx, 550, 560, 200, 50, 6, (40, 150, 70))
    text(ctx, "NOTAUSGANG", 650, 595, 26, (1, 1, 1))
    for x in (380, 920):
        ell(ctx, x, 560, 22, 14, (255, 240, 150), 4)
    # Bank + Mama
    if P.get("mama", True):
        rect(ctx, 260, 1700, 780, 60, (170, 120, 70))
        rect(ctx, 300, 1760, 30, 200, (120, 85, 50), 4)
        rect(ctx, 970, 1760, 30, 200, (120, 85, 50), 4)
        mv = P.get("mama_view", "back")
        person(ctx, LOOKS["MAMA"], 650, 1980 if mv == "back" else 2050, 0.95 if mv == "back" else 1.25,
               view=mv, pose="sit" if mv == "back" else "stand", t=t, talk=talk.get("MAMA", 0),
               expr=P.get("mama_expr", "sad"), arms=P.get("mama_arms", "hold_arm"), bandage=P.get("bandage", True))
    if P.get("dark", 0):
        ctx.set_source_rgba(0.05, 0.07, 0.12, P["dark"]); ctx.paint()


def helicopter(ctx, x, y, s, t):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -300, -120, 520, 240, 110, (210, 60, 50))
    poly(ctx, [(200, -60), (650, -40), (650, 10), (200, 60)], (210, 60, 50))
    rect(ctx, 600, -110, 40, 140, (210, 60, 50))
    rrect(ctx, -260, -90, 200, 120, 50, (160, 200, 225))
    rect(ctx, -60, -80, 160, 150, (235, 235, 235), 4)
    text(ctx, "+", 20, 30, 120, (0.85, 0.15, 0.15))
    line(ctx, -40, -120, -40, -170, 12)
    w = 700 * abs(math.cos(t * 40))
    line(ctx, -40 - w, -175, -40 + w, -175, 16)
    line(ctx, -250, 120, -250, 170, 8); line(ctx, 150, 120, 150, 170, 8)
    line(ctx, -330, 175, 230, 175, 10)
    ctx.restore()


def field(ctx, t, P, talk):
    g = cairo.LinearGradient(0, 0, 0, 1100)
    g.add_color_stop_rgb(0, 0.55, 0.62, 0.72); g.add_color_stop_rgb(1, 0.88, 0.8, 0.7)
    ctx.set_source(g); ctx.rectangle(-500, -500, SW + 1000, SH + 1000); ctx.fill()
    for k in range(10):
        ctx.set_source_rgba(0.3, 0.3, 0.32, 0.45)
        ell_path(ctx, 200 + k * 25, 950 - k * 80, 80 + k * 15, 70 + k * 10); ctx.fill()
    rect(ctx, -400, 900, 700, 250, (200, 190, 175))
    poly(ctx, [(-500, 1100), (SW + 500, 1100), (SW + 500, SH + 500), (-500, SH + 500)], (95, 160, 85))
    line(ctx, -500, 1350, SW + 500, 1350, 10, (1, 1, 1), 0.85)
    ctx.set_source_rgba(1, 1, 1, 0.85); ctx.set_line_width(10)
    ell_path(ctx, 650, 1350, 260, 80); ctx.stroke()
    # Zaun + Tor rechts
    for k in range(12):
        line(ctx, 900 + k * 50, 950, 900 + k * 50, 1180, 5)
    line(ctx, 880, 960, SW + 400, 960, 6); line(ctx, 880, 1100, SW + 400, 1100, 6)
    gate = P.get("gate", 0.0)   # 0 offen, 1 zu
    gx = 1050
    rect(ctx, gx - 10, 900, 20, 300, (80, 80, 85), 4)
    ctx.save(); ctx.translate(gx, 900); ctx.scale(gate * 1.0 + 0.05, 1)
    for k in range(6):
        line(ctx, k * 40, 0, k * 40, 290, 6)
    line(ctx, 0, 30, 240, 30, 8); line(ctx, 0, 260, 240, 260, 8)
    ctx.restore()
    # Horde
    for k in range(P.get("horde", 0)):
        x = 1120 + (k % 6) * 55 - P.get("horde_push", 0) * (1 - gate) * 200
        person(ctx, student_look(500 + k) if k % 3 else LOOKS["JANITOR"], x, 1150 + (k // 6) * 20, 0.16, t=t,
               inf=1, arms="reach", walk=0.6, seed=k)
    # Hubschrauber
    hy = P.get("heli_y", None)
    if hy is not None:
        helicopter(ctx, P.get("heli_x", 520), hy, P.get("heli_s", 0.9), t)
    # Soldaten
    for k in range(P.get("soldiers", 0)):
        person(ctx, LOOKS["SOLDAT"], 330 + k * 160, 1420, 0.3, t=t, talk=talk.get("SOLDAT", 0) if k == 0 else 0,
               arms="wave" if k == 0 else "down", expr="angry", seed=k)
    if P.get("noah_x", -1) >= 0:
        person(ctx, LOOKS["NOAH"], P["noah_x"], P.get("noah_y", 2250), P.get("noah_s", 1.0), t=t,
               talk=talk.get("NOAH", 0), expr=P.get("noah_expr", "sad"), arms=P.get("noah_arms", "hold_arm"),
               bite=P.get("noah_bite", True), inf=P.get("noah_inf", 0.25), view=P.get("noah_view", "front"),
               walk=P.get("noah_walk", 0))
    if P.get("mama_x", -1) >= 0:
        person(ctx, LOOKS["MAMA"], P["mama_x"], 2350, 1.0, t=t, talk=talk.get("MAMA", 0), expr="scared", bandage=True,
               arms="pull")
    if P.get("lea_x", -1) >= 0:
        person(ctx, LOOKS["LEA"], P["lea_x"], 2300, 0.9, t=t, talk=talk.get("LEA", 0), expr="scared", arms="down")


def heli_view(ctx, t, P, talk):
    """Blick aus dem Hubschrauber nach unten; P['alt'] 0..1 Höhe."""
    alt = P.get("alt", 0.0)
    s = 1.0 - alt * 0.75
    ctx.save()
    ctx.translate(650, 1250); ctx.scale(s, s); ctx.translate(-650, -1250)
    rect(ctx, -3000, -3000, 7300, 8300, (110, 150, 95))
    for k in range(-6, 8):
        rect(ctx, -3000, -1200 + k * 600, 7300, 60, (150, 150, 150), 3)
    for i in range(-4, 6):
        for j in range(-3, 5):
            if (i, j) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                continue
            rect(ctx, 650 + i * 650 - 200, 1250 + j * 600 - 180, 420, 340, (185, 180, 170))
    rect(ctx, 200, 700, 900, 1100, (95, 160, 85))
    ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(8)
    ctx.rectangle(260, 760, 780, 980); ctx.stroke()
    rect(ctx, 200, 300, 900, 350, (180, 90, 70))
    rect(ctx, 1150, 700, 350, 400, (170, 160, 150))
    line(ctx, 1100, 700, 1100, 1800, 8)
    # Horde am Tor
    for k in range(40):
        ctx.set_source_rgba(0.35, 0.4, 0.3, 1)
        ctx.arc(1160 + (k % 8) * 22, 1180 + (k // 8) * 24, 9, 0, 2 * math.pi); ctx.fill()
    # Noah
    person(ctx, LOOKS["NOAH"], 1080, 1300, 0.32, t=t, arms="wave", inf=0.3)
    ctx.restore()
    # Rauch über der Stadt
    for k in range(6):
        ctx.set_source_rgba(0.3, 0.3, 0.33, 0.25 + alt * 0.2)
        ell_path(ctx, 200 + k * 200, 300 + (k % 2) * 80, 200, 120); ctx.fill()
    # Hubschrauber-Türrahmen
    ctx.set_source_rgba(*C((40, 42, 46)))
    ctx.rectangle(-500, -500, 450, SH + 1000); ctx.fill()
    ctx.rectangle(SW - 50, -500, 600, SH + 1000); ctx.fill()
    ctx.rectangle(-500, -500, SW + 1000, 520); ctx.fill()
    rect(ctx, -60, 0, 30, SH, (200, 200, 200), 4)
    line(ctx, 100, 20, 100, SH, 14, (0.85, 0.75, 0.2))


def black(ctx, t, P, talk):
    ctx.set_source_rgb(0, 0, 0); ctx.paint()


SCENES = dict(classroom=classroom, hallway=hallway, stairs=stairs, steeldoor=steeldoor, shelter=shelter, yard=yard,
              car_inside=car_inside, gym=gym, field=field, heli_view=heli_view, black=black)

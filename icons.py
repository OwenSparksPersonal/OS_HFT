"""Position icons: geometry plus export as PNG (for the workbook) and SVG (for apps).

Two styles, same file names and colours:
  "v1" - the original line figures, in icons/
  "v2" - filled pictograms with a rifle silhouette, in icons/v2/

Geometry is on a 96 x 96 grid. Item kinds:
  ("L", [(x, y), ...], width[, colour])  polyline with round caps and joins
  ("C", cx, cy, r, width[, colour])      circle outline; r is the outer radius
  ("F", cx, cy, r)                       filled circle in the icon colour
  ("P", [(x, y), ...][, colour])         filled polygon
  ("X", item, pad)                       erase `item` grown by `pad` from everything drawn before it
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
ICONS = BASE / "icons"
SVG_SIZES = (24, 48, 96)
S = 6  # supersample

NEUTRAL=(34,34,34,255); BLUE=(24,95,165,255); AMBER=(186,117,23,255)
GR = (170,170,170,255)
WH=(255,255,255,255)

# ---- v1: line figures ----

ground = ("L", [(6,86),(90,86)], 2.5, GR)
prone = [ground, ("C",42,72,6,5), ("L",[(8,82),(34,77)],5), ("L",[(30,74),(90,68)],5),
         ("L",[(34,77),(62,77)],5), ("L",[(64,86),(64,73)],6)]
badge = [("F",80,16,12), ("L",[(80,10),(80,22)],4,WH), ("L",[(75,17),(80,22),(85,17)],4,WH)]
pone = prone + badge
us = [ground, ("C",40,18,6,5), ("L",[(40,25),(40,54)],5), ("L",[(40,54),(32,86)],5), ("L",[(40,54),(48,86)],5),
      ("L",[(34,34),(90,30)],5), ("L",[(40,36),(60,32.5)],5), ("L",[(40,36),(35,41)],5), ("L",[(60,86),(60,80)],7)]
uk = [ground, ("C",42,34,6,5), ("L",[(42,41),(38,62)],5), ("L",[(38,62),(32,86),(16,86)],5),
      ("L",[(38,62),(58,66),(58,86),(66,86)],5), ("L",[(44,46),(92,40)],5), ("L",[(42,48),(66,43)],5)]
ss = [ground, ("C",36,18,6,5), ("L",[(36,25),(36,54)],5), ("L",[(36,54),(28,86)],5), ("L",[(36,54),(44,86)],5),
      ("L",[(30,34),(86,30)],5), ("L",[(36,36),(54,32.5)],5), ("L",[(36,36),(31,41)],5),
      ("L",[(72,86),(72,35)],6), ("L",[(65,35),(79,35)],6)]
sk = [ground, ("C",36,34,6,5), ("L",[(36,41),(32,62)],5), ("L",[(32,62),(26,86),(10,86)],5),
      ("L",[(32,62),(50,66),(50,86),(58,86)],5), ("L",[(38,46),(84,40)],5), ("L",[(36,48),(58,43)],5),
      ("L",[(74,86),(74,47)],6), ("L",[(67,47),(81,47)],6)]

# ---- v2: filled pictograms ----

GAP = 1.6  # knockout around the rifle and the badge

# One colour per position, all at the same relative luminance (~0.20) so each has about
# 4.2:1 contrast on white and 3.9:1 on #1e1e1e (>= 3:1 on dark greys up to #2b2b2b).
V2_GREEN=(48,140,67,255); V2_AMBER=(185,102,12,255); V2_RED=(218,70,70,255)
V2_MAGENTA=(202,70,166,255); V2_BLUE=(58,123,211,255); V2_TEAL=(18,136,146,255)
V2_GREY=(123,123,123,255)  # posts and ground, same luminance

def _place(pts, x, y, ang, sc):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(round(x + sc*(px*c - py*s), 2), round(y + sc*(px*s + py*c), 2)) for px, py in pts]

def rifle(x, y, ang=0, sc=1.0):
    """Scoped air rifle pointing right, butt centre at (x, y); ang in degrees (negative = muzzle up)."""
    p = lambda pts: _place(pts, x, y, ang, sc)
    parts = [("P", p([(0,-3.5),(38,-2.2),(38,1.8),(17,2.4),(14.5,8),(10.5,8),(11.5,3),(0,5)])),  # stock + action
             ("L", p([(37,-0.2),(58,-0.2)]), 3.4*sc),                                              # barrel
             ("L", p([(19,-6.2),(36,-6.2)]), 3.6*sc),                                              # scope tube
             ("L", p([(37.5,-6.6),(40,-6.6)]), 6*sc),                                              # objective bell
             ("L", p([(23.5,-6),(23.5,-2.5)]), 2.2*sc), ("L", p([(32,-6),(32,-2.5)]), 2.2*sc)]      # mounts
    return [("X", it, GAP) for it in parts] + parts

def figure(head, torso, limbs):
    """head: (cx, cy, r); torso: [(x, y), ...] hips -> shoulders; limbs: [(points, width), ...]."""
    return [("F", *head), ("L", torso, 11)] + [("L", pts, w) for pts, w in limbs]

def post(x, top, w=10):
    """Square-cut post (x = left edge), set apart from the figure by a gap."""
    return [("X", ("P", [(x, top), (x+w, top), (x+w, 80), (x, 80)]), GAP),
            ("P", [(x, top), (x+w, top), (x+w, 88), (x, 88)], V2_GREY)]

ground2 = ("L", [(4,87),(92,87)], 2, V2_GREY)
badge2 = [("X", ("F",80,15,12), GAP), ("F",80,15,12),
          ("L",[(80,9),(80,21)],4,WH), ("L",[(75,16),(80,21),(85,16)],4,WH)]

prone2 = [ground2] + figure(
    (50,57,6.5), [(26,79),(45,71)],
    [([(26,80),(14,83),(4,84)], 8),            # legs
     ([(47,72),(57,83)], 7), ([(57,83),(66,71)], 6),  # front arm: elbow on the ground, hand up
     ([(46,71),(44,79),(52,74)], 6)]) + rifle(43, 68, -4, 0.86)
pone2 = prone2 + badge2

us2 = [ground2] + figure(
    (43,15,6.5), [(36,53),(38,30)],
    [([(36,54),(30,70),(27,86)], 8), ([(36,54),(43,70),(46,86)], 8),   # legs
     ([(40,30),(47,43)], 7), ([(47,43),(57,33)], 6),                    # front arm under the fore-end
     ([(36,30),(29,37)], 7), ([(29,37),(46,35)], 6)]) + rifle(37, 28, -3, 0.95)

uk2 = [ground2] + figure(
    (41,30,6.5), [(30,64),(35,44)],
    [([(30,65),(46,85),(24,86)], 8),                          # rear leg: knee down, sitting on the heel
     ([(31,64),(54,60)], 8), ([(54,60),(56,86)], 7),          # front leg, foot planted
     ([(37,45),(52,56)], 7), ([(52,56),(60,45)], 6),          # front elbow on the knee
     ([(33,46),(27,52)], 7), ([(27,52),(45,50)], 6)]) + rifle(34, 43, -4, 0.92)

ss2 = [ground2] + figure(
    (34,15,6.5), [(27,53),(29,30)],
    [([(27,54),(21,70),(18,86)], 8), ([(27,54),(34,70),(37,86)], 8),
     ([(31,30),(45,40)], 7), ([(45,40),(65,33)], 6),          # front hand on the post
     ([(27,30),(20,37)], 7), ([(20,37),(37,35)], 6)]) + post(62, 38) + rifle(28, 28, -3, 0.95)

sk2 = [ground2] + figure(
    (32,31,6.5), [(21,65),(26,45)],
    [([(21,66),(37,85),(15,86)], 8),
     ([(22,65),(45,61)], 8), ([(45,61),(47,86)], 7),
     ([(28,46),(43,56)], 7), ([(43,56),(62,49)], 6),          # front hand on the post
     ([(24,47),(18,53)], 7), ([(18,53),(36,51)], 6)]) + post(59, 54) + rifle(25, 44, -3, 0.95)

STYLES = {
    "v1": (ICONS, {"Prone":("pr",prone,NEUTRAL), "Prone only":("po",pone,AMBER),
                   "Unsupported standing":("us",us,NEUTRAL), "Unsupported kneeling":("uk",uk,NEUTRAL),
                   "Supported standing":("ss",ss,BLUE), "Supported kneeling":("sk",sk,BLUE)}),
    "v2": (ICONS / "v2", {"Prone":("pr",prone2,V2_GREEN), "Prone only":("po",pone2,V2_AMBER),
                          "Unsupported standing":("us",us2,V2_RED), "Unsupported kneeling":("uk",uk2,V2_MAGENTA),
                          "Supported standing":("ss",ss2,V2_BLUE), "Supported kneeling":("sk",sk2,V2_TEAL)}),
}
# position -> (file name, geometry, colour), for the original style
ICON_SET = STYLES["v1"][1]

def _colour(it, color):
    return it[-1] if isinstance(it[-1], tuple) else color

def _grow(it, pad):
    """The shape of `it` enlarged by `pad` on every side, as a list of items."""
    kind = it[0]
    if kind == "L":
        return [("L", it[1], it[2] + 2*pad)]
    if kind == "F":
        return [("F", it[1], it[2], it[3] + pad)]
    if kind == "C":
        return [("C", it[1], it[2], it[3] + pad, it[4] + 2*pad)]
    pts = it[1]
    return [("P", pts), ("L", pts + [pts[0]], 2*pad)]

def draw_png(path, items, color):
    img = Image.new("RGBA", (96*S, 96*S), (0,0,0,0))
    d = ImageDraw.Draw(img)
    def line(pts, w, col):
        p = [(x*S, y*S) for x, y in pts]
        d.line(p, fill=col, width=int(w*S), joint="curve")
        r = w*S/2
        for x, y in p:
            d.ellipse([x-r, y-r, x+r, y+r], fill=col)
    def circ(cx, cy, r, w, col):
        d.ellipse([(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], outline=col, width=int(w*S))
    def shape(it, col):
        kind = it[0]
        if kind == "F":
            r = it[3]*S; d.ellipse([it[1]*S-r, it[2]*S-r, it[1]*S+r, it[2]*S+r], fill=col)
        elif kind == "L":
            line(it[1], it[2], col)
        elif kind == "P":
            d.polygon([(x*S, y*S) for x, y in it[1]], fill=col)
        else:
            circ(it[1], it[2], it[3], it[4], col)
    for it in items:
        if it[0] == "X":
            for g in _grow(it[1], it[2]):
                shape(g, (0,0,0,0))  # ImageDraw writes RGBA without blending, so this clears
        else:
            shape(it, color if it[0] == "F" else _colour(it, color))
    img = img.resize((96, 96), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)

def _hex(c):
    return "#%02x%02x%02x" % c[:3]

def _n(v):
    return f"{v:g}"

def _svg_shape(it, col):
    kind = it[0]
    if kind == "F":
        return f'<circle cx="{_n(it[1])}" cy="{_n(it[2])}" r="{_n(it[3])}" fill="{col}"/>'
    if kind == "L":
        pts = " ".join(f"{_n(x)},{_n(y)}" for x, y in it[1])
        return (f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{_n(it[2])}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "P":
        pts = " ".join(f"{_n(x)},{_n(y)}" for x, y in it[1])
        return f'<polygon points="{pts}" fill="{col}"/>'
    # Pillow draws the outline inside the radius; SVG centres the stroke on it.
    _, cx, cy, r, w = it[:5]
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r - w/2)}" fill="none" stroke="{col}" stroke-width="{_n(w)}"/>'

def svg_shapes(items, color, prefix="m"):
    """SVG elements for one icon, in 96 x 96 user units. Each run of "X" items becomes a
    mask over everything drawn before it; mask ids start with `prefix`."""
    out, i, k = [], 0, 0
    while i < len(items):
        it = items[i]
        if it[0] != "X":
            out.append(_svg_shape(it, _hex(color if it[0] == "F" else _colour(it, color))))
            i += 1
            continue
        holes = []
        while i < len(items) and items[i][0] == "X":
            holes += [_svg_shape(g, "#000") for g in _grow(items[i][1], items[i][2])]
            i += 1
        mid = f"{prefix}-{k}"; k += 1
        out = [f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="96" height="96">'
               f'<rect width="96" height="96" fill="#fff"/>{"".join(holes)}</mask>',
               f'<g mask="url(#{mid})">{"".join(out)}</g>']
    return out

def svg_icon(pos, size, style="v1"):
    name, items, color = STYLES[style][1][pos]
    body = "\n  ".join(svg_shapes(items, color, f"hft-{name}"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 96 96" '
            f'role="img" aria-label="{pos}">\n  <title>{pos}</title>\n  {body}\n</svg>\n')

def svg_sprite(style="v1"):
    """<symbol> sprite: <svg><use href="#hft-pr"/></svg>. Hidden by zero size, not display:none,
    which stops browsers applying the v2 masks."""
    syms = []
    for pos, (name, items, color) in STYLES[style][1].items():
        body = "\n    ".join(svg_shapes(items, color, f"hft-{name}"))
        syms.append(f'  <symbol id="hft-{name}" viewBox="0 0 96 96">\n    <title>{pos}</title>\n    {body}\n  </symbol>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" aria-hidden="true" '
            'style="position:absolute;overflow:hidden">\n'
            + "\n".join(syms) + "\n</svg>\n")

def export_all():
    for style, (folder, icon_set) in STYLES.items():
        for pos, (name, items, color) in icon_set.items():
            draw_png(folder / f"{name}.png", items, color)
            for size in SVG_SIZES:
                d = folder / "svg" / str(size)
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{name}.svg").write_text(svg_icon(pos, size, style), encoding="utf-8")
        (folder / "svg" / "sprite.svg").write_text(svg_sprite(style), encoding="utf-8")

if __name__ == "__main__":
    export_all()

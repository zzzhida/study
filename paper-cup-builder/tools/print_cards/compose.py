"""Lays out the rendered views as 12 A4 pages (one group per page, three strips with cut lines).

    python3 tools/print_cards/compose.py        (after render.js; run from the paper-cup-builder folder)

Output: tools/print_cards/out/contest_cards_A4.pdf (300 dpi). Print at 100% / actual size.
"""
import json
import pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
IDS = [f"r{r}g{g}" for r in (1, 2) for g in range(1, 7)]
PW, PH = 2480, 3508                      # A4 at 300 dpi
SH = PH // 3                             # three equal strips
IW, IH = 2240, 1000
X0 = (PW - IW) // 2
GROUND = "#7f8487"

FONT_CANDIDATES = [  # a font with Chinese glyphs: Linux, Windows, macOS
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-{w}.ttc", 2),
    ("C:/Windows/Fonts/msyh{wb}.ttc", 0),
    ("/System/Library/Fonts/PingFang.ttc", 0),
]


def font(weight, size):
    for pattern, index in FONT_CANDIDATES:
        p = pattern.format(w=weight, wb="bd" if weight == "Bold" else "")
        if pathlib.Path(p).exists():
            return ImageFont.truetype(p, size, index=index)
    return ImageFont.load_default()


def scissors(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/seguisym.ttf"):
        if pathlib.Path(p).exists():
            return ImageFont.truetype(p, size)
    return None


def group_name(gid):
    return f"第{'一' if gid[1] == '1' else '二'}轮 · 第 {gid[3]} 组"


def main():
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))
    sym = scissors(54)
    pages = []
    for gid in IDS:
        g = meta["groups"][gid]
        cm = g["cmPerPx"]
        page = Image.new("RGB", (PW, PH), "white")
        d = ImageDraw.Draw(page)
        side = "左" if g["side"] == "L" else "右"
        views = [("front", "正视"), ("side", f"侧视（从正视的{side}手边看）"), ("top", "俯视（图片下方 = 正视方向）")]
        for k, (view, label) in enumerate(views):
            y0 = k * SH
            d.text((X0, y0 + 38), group_name(gid), font=font("Bold", 46), fill="#222")
            lf = font("Medium", 42)
            d.text((X0 + IW - d.textlength(label, font=lf), y0 + 42), label, font=lf, fill="#333")
            im = Image.open(OUT / f"{gid}_{view}.png").convert("RGB")
            if view != "top":  # table line: the floor sits 2.2 cm above the bottom edge of the render
                gy = round(IH - 2.2 / cm)
                ImageDraw.Draw(im).line([(0, gy), (IW, gy)], fill=GROUND, width=4)
            page.paste(im, (X0, y0 + 118))
            d.rectangle([X0, y0 + 118, X0 + IW - 1, y0 + 118 + IH - 1], outline="#9aa0a3", width=2)
        for k in (1, 2):  # dashed cut lines between the strips
            y = k * SH
            for x in range(150, PW - 60, 44):
                d.line([(x, y), (min(x + 24, PW - 60), y)], fill="#666", width=3)
            if sym:
                d.text((60, y - 34), "✂", font=sym, fill="#444")
        pages.append(page)
    out = OUT / "contest_cards_A4.pdf"
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=300)
    print(f"wrote {out.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()

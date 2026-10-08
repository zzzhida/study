"""Pack index.html, vendor/ and img/ into one self-contained HTML file that works offline.

Usage (from the paper-cup-builder folder):
    python3 tools/build_offline.py
Output: dist/paper-cup-builder-offline.html
"""
import base64
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "paper-cup-builder-offline.html"


def inline_js(code: str) -> str:
    return "<script>" + code.replace("</script", "<\\/script") + "</script>"


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # web fonts are optional (the page falls back to system fonts); drop them so nothing touches the network
    html = "\n".join(line for line in html.split("\n") if "fonts.googleapis.com" not in line and "fonts.gstatic.com" not in line)

    images = {
        "img/" + p.name: "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
        for p in sorted((ROOT / "img").glob("*.jpg"))
    }
    three = (ROOT / "vendor" / "three.min.js").read_text(encoding="utf-8")
    orbit = (ROOT / "vendor" / "OrbitControls.js").read_text(encoding="utf-8")

    tag_three = '<script src="vendor/three.min.js"></script>'
    tag_orbit = '<script src="vendor/OrbitControls.js"></script>'
    photo_src = "img.src = p.photos + v + '.jpg';"
    for needle in (tag_three, tag_orbit, photo_src):
        if html.count(needle) != 1:
            raise SystemExit(f"index.html changed, cannot find: {needle}")

    html = html.replace(tag_three, inline_js(three) + "\n<script>window.__IMG=" + json.dumps(images) + ";</script>")
    html = html.replace(tag_orbit, inline_js(orbit))
    html = html.replace(photo_src, "img.src = (window.__IMG && window.__IMG[p.photos + v + '.jpg']) || (p.photos + v + '.jpg');")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()

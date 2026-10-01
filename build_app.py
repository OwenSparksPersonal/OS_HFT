"""Build the scorecard web app: inlines the course and the v2 icon sprite into one HTML page."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parent

ap = argparse.ArgumentParser()
ap.add_argument("--course", default=ROOT / "course.json", type=Path)
ap.add_argument("--out", default=ROOT / "app" / "scorecard.html", type=Path)
args = ap.parse_args()

course = json.loads(args.course.read_text(encoding="utf-8"))
sprite = (ROOT / "icons" / "v2" / "svg" / "sprite.svg").read_text(encoding="utf-8")
template = (ROOT / "app" / "scorecard.template.html").read_text(encoding="utf-8")

html = template.replace("<!--SPRITE-->", sprite.strip()).replace("/*COURSE*/[]", json.dumps(course))
args.out.write_text(html, encoding="utf-8")
print(f"Wrote {args.out}")

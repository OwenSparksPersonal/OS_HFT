"""Generate a random 30-shot course that passes every check in rules.CHECKS.

    python generate.py [--seed N] [--out course_generated.json]
    python build.py --course course_generated.json --out generated.xlsx

Follows the decisions in CLAUDE.md: Table 3 Option 2 for supported kneeling, and
Prone Only on one small (15-19mm), one medium (20-34mm) and one large (35-45mm) target.
The Table 1A option and the 15-19mm count are picked at random.
Distances are whole yards, so 35.01-40 yd becomes 36-40 yd.
"""
import argparse
import json
import random
from pathlib import Path

from rules import SMALL, MID, NEAR, FAR, LARGE, POS_LARGE, POS_MED, Band, validate, is_compliant

BASE = Path(__file__).resolve().parent

def pick(rng, band: Band):
    lo = int(band.yd_lo) + 1 if band.yd_above else int(band.yd_lo)
    return {"range_yd": rng.randint(lo, int(band.yd_hi)), "hit_zone_mm": rng.randint(band.mm_lo, band.mm_hi)}

def generate(rng):
    n_mid, n_far = rng.choice([(2, 4), (3, 3)])  # Table 1A Option 1 or 2
    n_small = rng.randint(4, 6)
    n_large = 24 - n_small - n_mid - 4 - n_far
    prone = {"small": [SMALL] * n_small, "medium": [MID] * n_mid + [NEAR] * 4 + [FAR] * n_far,
             "large": [LARGE] * n_large}
    shots = []
    for bands in prone.values():
        group = [dict(position="Prone", **pick(rng, b)) for b in bands]
        rng.choice(group)["position"] = "Prone only"
        shots += group
    for pos, band in [("Unsupported standing", POS_LARGE), ("Unsupported kneeling", POS_LARGE),
                      ("Supported standing", rng.choice([POS_MED, POS_LARGE])),
                      ("Supported standing", rng.choice([POS_MED, POS_LARGE])),
                      ("Supported kneeling", POS_MED), ("Supported kneeling", POS_LARGE)]:
        shots.append(dict(position=pos, **pick(rng, band)))
    rng.shuffle(shots)
    return [{"shot": i, **s} for i, s in enumerate(shots, 1)]

def main():
    ap = argparse.ArgumentParser(description="Generate a random UKAHFT-compliant course.")
    ap.add_argument("--seed", type=int, help="random seed, for a reproducible course")
    ap.add_argument("--out", type=Path, default=BASE / "course_generated.json",
                    help="output JSON (default: course_generated.json)")
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    shots = generate(random.Random(seed))
    if not is_compliant(shots):  # the generator has a bug if this ever fires
        errors, results = validate(shots)
        raise SystemExit("generated course failed: " + "; ".join(
            errors + [f"{c.name} = {n}" for c, n, ok in results if not ok]))
    args.out.write_text(json.dumps(shots, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out.name} (seed {seed})")

if __name__ == "__main__":
    main()

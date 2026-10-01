"""UKAHFT course rules as data. CHECKS drives both the workbook's Checks sheet
(Excel formulas) and validate() (Python), so the two cannot drift apart.

Run as a script to validate a course file:  python rules.py [course.json]
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path

PRONE = ("Prone", "Prone only")
POSITIONS = PRONE + ("Unsupported standing", "Unsupported kneeling",
                     "Supported standing", "Supported kneeling")
N_SHOTS = 30

@dataclass(frozen=True)
class Band:
    """Hit zone mm_lo-mm_hi at yd_lo-yd_hi, inclusive. yd_above=True makes the lower bound exclusive (35.01-40 yd)."""
    mm_lo: int
    mm_hi: int
    yd_lo: float
    yd_hi: float
    yd_above: bool = False

    def __contains__(self, shot):
        mm, yd = shot["hit_zone_mm"], shot["range_yd"]
        lo_ok = yd > self.yd_lo if self.yd_above else yd >= self.yd_lo
        return self.mm_lo <= mm <= self.mm_hi and lo_ok and yd <= self.yd_hi

@dataclass(frozen=True)
class Check:
    """Count shots whose position is in `positions` (None = any) and that fit any of `bands`
    (empty = no size/range condition); or, with `sum_of`, add up other checks' counts."""
    name: str
    lo: int
    hi: int
    positions: tuple = None
    bands: tuple = ()
    sum_of: tuple = ()

SMALL = Band(15, 19, 13, 25)
MID = Band(20, 24, 8, 30)
NEAR = Band(25, 34, 8, 35)
FAR = Band(25, 34, 35, 40, yd_above=True)
LARGE = Band(35, 45, 8, 45)
POS_LARGE = Band(35, 45, 8, 35)   # positional 35-45mm, 8-35 yd
POS_MED = Band(25, 34, 8, 30)     # positional 25-34mm, 8-30 yd

CHECKS = [
    Check("Total shots", 30, 30),
    Check("Prone shots (incl. Prone only)", 24, 24, PRONE),
    Check("Prone only shots", 3, 3, ("Prone only",)),
    Check("Prone: 15-19mm at 13-25 yd", 4, 6, PRONE, (SMALL,)),
    Check("Prone: 20-24mm at 8-30 yd", 2, 3, PRONE, (MID,)),
    Check("Prone: 25-34mm at 8-35 yd", 4, 4, PRONE, (NEAR,)),
    Check("Prone: 25-34mm at 35.01-40 yd", 3, 4, PRONE, (FAR,)),
    Check("Prone: 35-45mm at 8-45 yd", 0, 24, PRONE, (LARGE,)),
    Check("Prone: every prone shot fits a band above", 24, 24,
          sum_of=("Prone: 15-19mm at 13-25 yd", "Prone: 20-24mm at 8-30 yd", "Prone: 25-34mm at 8-35 yd",
                  "Prone: 25-34mm at 35.01-40 yd", "Prone: 35-45mm at 8-45 yd")),
    # Table 1A allows (2 x 20-24mm, 4 far) or (3 x 20-24mm, 3 far); both total 6.
    Check("Table 1A: 20-24mm + 25-34mm at 35.01-40 yd", 6, 6,
          sum_of=("Prone: 20-24mm at 8-30 yd", "Prone: 25-34mm at 35.01-40 yd")),
    Check("Unsupported standing: 35-45mm at 8-35 yd", 1, 1, ("Unsupported standing",), (POS_LARGE,)),
    Check("Unsupported kneeling: 35-45mm at 8-35 yd", 1, 1, ("Unsupported kneeling",), (POS_LARGE,)),
    Check("Supported standing: valid targets", 2, 2, ("Supported standing",), (POS_MED, POS_LARGE)),
    Check("Supported kneeling: 25-34mm at 8-30 yd", 1, 1, ("Supported kneeling",), (POS_MED,)),
    Check("Supported kneeling: 35-45mm at 8-35 yd", 1, 1, ("Supported kneeling",), (POS_LARGE,)),
]

# ---- Excel ----

def excel_formula(check, P, D, Fz, row_of):
    """Formula for the Actual column. P/D/Fz are the position/yards/size ranges;
    row_of maps a check name to its Checks-sheet row (for sum_of)."""
    if check.sum_of:
        return "=" + "+".join(f"D{row_of[n]}" for n in check.sum_of)
    if check.positions is None:
        return f"=COUNTA({P})"
    if len(check.positions) == 1 and not check.bands:
        return f'=COUNTIF({P},"{check.positions[0]}")'
    pos = "+".join(f'({P}="{p}")' for p in check.positions)
    terms = [f"({pos})" if len(check.positions) > 1 else pos]
    if check.bands:
        bands = [f"({Fz}>={b.mm_lo})*({Fz}<={b.mm_hi})*({D}{'>' if b.yd_above else '>='}{b.yd_lo:g})*({D}<={b.yd_hi:g})"
                 for b in check.bands]
        terms.append(bands[0] if len(bands) == 1 else "(" + "+".join(f"({b})" for b in bands) + ")")
    return f"=SUMPRODUCT({'*'.join(terms)})"

# ---- Python validator ----

def count(check, shots, actual):
    if check.sum_of:
        return sum(actual[n] for n in check.sum_of)
    return sum(1 for s in shots
               if (check.positions is None or s["position"] in check.positions)
               and (not check.bands or any(s in b for b in check.bands)))

def validate(shots):
    """Return (errors, results). errors: problems with the data itself.
    results: (check, actual, ok) per CHECKS row, mirroring the Checks sheet."""
    errors = []
    if [s.get("shot") for s in shots] != list(range(1, len(shots) + 1)):
        errors.append("shot numbers must run 1, 2, 3, ... in order")
    for s in shots:
        if s.get("position") not in POSITIONS:
            errors.append(f"shot {s.get('shot')}: unknown position {s.get('position')!r}")
        for k in ("range_yd", "hit_zone_mm"):
            if not isinstance(s.get(k), (int, float)) or isinstance(s.get(k), bool):
                errors.append(f"shot {s.get('shot')}: {k} must be a number")
    if errors:
        return errors, []
    actual, results = {}, []
    for c in CHECKS:
        actual[c.name] = n = count(c, shots, actual)
        results.append((c, n, c.lo <= n <= c.hi))
    return errors, results

def is_compliant(shots):
    errors, results = validate(shots)
    return not errors and all(ok for _, _, ok in results)

def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent / "course.json"
    shots = json.loads(path.read_text(encoding="utf-8"))
    errors, results = validate(shots)
    for e in errors:
        print("ERROR", e)
    for c, n, ok in results:
        print(f"{'OK   ' if ok else 'CHECK'} {c.name:<48} {n:>3}  (min {c.lo}, max {c.hi})")
    good = not errors and all(ok for _, _, ok in results)
    print(f"{path.name}: {'compliant' if good else 'NOT compliant'}")
    return 0 if good else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

import argparse
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from icons import STYLES, export_all
from rules import CHECKS, excel_formula, validate

BASE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description="Build the UKAHFT course of fire workbook.")
ap.add_argument("--course", type=Path, default=BASE / "course.json", help="course JSON (default: course.json)")
ap.add_argument("--out", type=Path, default=BASE / "UKAHFT_course_of_fire.xlsx", help="output workbook")
ap.add_argument("--icons", choices=sorted(STYLES), default="v2", help="icon set: v1 line figures, v2 pictograms (default)")
args = ap.parse_args()

export_all()
icon_dir, icons = STYLES[args.icons]

with open(args.course) as fh:
    _c = json.load(fh)
errors, results = validate(_c)
for e in errors:
    print("ERROR", e)
for c, n, ok in results:
    if not ok:
        print(f"CHECK {c.name}: {n} (min {c.lo}, max {c.hi})")
if errors:
    raise SystemExit(1)
shots = [(r["position"], r["range_yd"], r["hit_zone_mm"]) for r in _c]
assert len(shots) == 30

F = "Arial"
hdr_fill = PatternFill("solid", fgColor="1F3864")
thin = Side(style="thin", color="BFBFBF")
border = Border(bottom=thin)

wb = Workbook()
ws = wb.active
ws.title = "Course of fire"
heads = ["Shot","Icon","Position","Range (yd)","Range (m)","Target type"]
for c,h in enumerate(heads,1):
    cell = ws.cell(row=1,column=c,value=h)
    cell.font = Font(name=F,bold=True,color="FFFFFF",size=11)
    cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="center" if c in (1,2) else ("left" if c==3 else "right" if c in (4,5) else "center"), vertical="center")
ws.row_dimensions[1].height = 24

for i,(pos,yd,mm) in enumerate(shots):
    r = i+2
    ws.row_dimensions[r].height = 42
    vals = [i+1, None, pos, yd, f"=ROUND(D{r}*Checks!$B$3,2)", mm]
    for c,v in enumerate(vals,1):
        cell = ws.cell(row=r,column=c,value=v)
        cell.font = Font(name=F,size=11, color="0000FF" if c in (4,6) else "000000")
        cell.border = border
        cell.alignment = Alignment(vertical="center",
            horizontal="center" if c in (1,6) else ("left" if c==3 else "right"))
    ws.cell(row=r,column=5).number_format = "0.00"
    ws.cell(row=r,column=6).number_format = '0"mm"'
    ws.cell(row=r,column=6).alignment = Alignment(horizontal="center",vertical="center")
    img = XLImage(str(icon_dir / f"{icons[pos][0]}.png"))
    img.width = img.height = 40
    ws.add_image(img, f"B{r}")

for col,w in zip("ABCDEF",[8,8,24,13,13,14]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A2"
ws["H1"] = "Notes"
ws["H1"].font = Font(name=F,bold=True)
notes = ["Blue text = input values (position, range, hit zone size).",
         "Range (m) is calculated from yards using the factor on the Checks sheet.",
         "Icon colours: black = unsupported/prone, blue = supported, amber = prone only.",
         "Source: UKAHFT Rules and Course Setting Guidelines, REV 01.2 (28.05.2020).",
         "Prone targets need 10mm minimum faceplate; positional targets 20mm."]
for i,n in enumerate(notes):
    ws.cell(row=2+i,column=8,value=n).font = Font(name=F,size=10,color="595959")
ws.column_dimensions["H"].width = 70

# Checks sheet
ck = wb.create_sheet("Checks")
ck["A1"] = "Rule compliance checks"; ck["A1"].font = Font(name=F,bold=True,size=13)
ck["A3"] = "Yards to metres factor"; ck["B3"] = 0.9144
ck["B3"].font = Font(name=F,color="0000FF"); ck["B3"].number_format = "0.0000"
ck["C3"] = "Standard definition: 1 yd = 0.9144 m"; ck["C3"].font = Font(name=F,size=10,color="595959")
ck["A3"].font = Font(name=F)

for c,h in enumerate(["Check","Min","Max","Actual","Result"],1):
    cell = ck.cell(row=5,column=c,value=h)
    cell.font = Font(name=F,bold=True,color="FFFFFF"); cell.fill = hdr_fill
    cell.alignment = Alignment(horizontal="left" if c==1 else "center")

P = "'Course of fire'!$C$2:$C$31"
D = "'Course of fire'!$D$2:$D$31"
Fz = "'Course of fire'!$F$2:$F$31"
r0 = 6
row_of = {c.name: r0+i for i,c in enumerate(CHECKS)}
for i,c in enumerate(CHECKS):
    r = r0+i
    ck.cell(row=r,column=1,value=c.name).font = Font(name=F)
    ck.cell(row=r,column=2,value=c.lo).font = Font(name=F,color="0000FF")
    ck.cell(row=r,column=3,value=c.hi).font = Font(name=F,color="0000FF")
    ck.cell(row=r,column=4,value=excel_formula(c, P, D, Fz, row_of))
    ck.cell(row=r,column=5,value=f'=IF(AND(D{r}>=B{r},D{r}<=C{r}),"OK","CHECK")')
    for col in (2,3,4,5):
        ck.cell(row=r,column=col).alignment = Alignment(horizontal="center")
        if col in (4,5): ck.cell(row=r,column=col).font = Font(name=F, bold=(col==5))
ck.column_dimensions["A"].width = 46
for col in "BCDE": ck.column_dimensions[col].width = 12
ck.column_dimensions["C"].width = 12
ck.cell(row=r0+len(CHECKS)+1,column=1,
  value="Prone band counts use Table 1/1A (Option 1: 2 x 20-24mm + 4 far 25-34mm, or Option 2: 3 + 3). Supported kneeling uses Table 3 Option 2.").font = Font(name=F,size=10,color="595959")

wb.save(args.out)
print(f"Wrote {args.out.name}" + ("" if all(ok for _,_,ok in results) else " (some checks fail)"))

# -*- coding: utf-8 -*-
"""Verify candidate chemical structures (SMILES) against reported molecular
formulas and/or HRMS m/z values, and optionally render 2D depictions for
visual comparison with scheme figures.

Typical use after reading a synthesis/characterization section:

  1. Render the scheme page at high DPI and identify connectivity.
  2. Propose SMILES for each compound (hand-written or programmatically
     assembled for homologous series).
  3. Run this tool to check formula + exact mass vs SI HRMS.
  4. Render 2D depictions and compare against the scheme image.

Requires: rdkit. Read-only with respect to source documents.

CLI examples:

  python chem_structure_verify.py --smiles "Cc1cc(C)c(C2=C3C=CC=[N+]3[B-](F)(F)n3cccc32)c(C)c1" \
      --formula C18H17BF2N2 --depict M.png

  python chem_structure_verify.py --batch compounds.csv --json-report report.json

Batch CSV columns: name, smiles, formula (optional), ion (optional), mz (optional)
Ion species supported: [M]+, [M]-, [M]+., [M+H]+, [M-H]-, [M+Na]+, [M+K]+,
[M-F]+, [M-F]-, [M+Cl]-, [M+NH4]+
"""
import argparse
import csv
import json
import re
import sys

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors, Draw
except ImportError:
    sys.stderr.write(
        "ERROR: rdkit is required. Install with: pip install rdkit\n"
    )
    sys.exit(2)

# Monoisotopic (most-abundant-isotope) masses matching RDKit defaults used by
# CalcExactMolWt (11B, 35Cl, ...). Adduct/loss masses for ion bookkeeping.
ION_ADJUST = {
    "[M]+": 0.0,
    "[M]+.": 0.0,
    "[M]-": 0.0,
    "[M+H]+": 1.007276,
    "[M+NH4]+": 18.033823,
    "[M+Na]+": 22.989218,
    "[M+K]+": 38.963158,
    "[M-H]-": -1.007276,
    "[M-F]+": -18.998403,
    "[M-F]-": -18.998403,
    "[M+Cl]-": 34.968853,
}

FORMULA_RE = re.compile(r"([A-Z][a-z]?)(\d*)")


def formula_ok(computed, expected):
    def parse(f):
        return {el: int(n) if n else 1 for el, n in FORMULA_RE.findall(f)}
    return parse(computed) == parse(expected)


def verify_one(name, smiles, expected_formula=None, ion=None, mz=None,
               tol_da=0.01, depict=None):
    rec = {"name": name, "smiles": smiles}
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        rec.update(parse_ok=False, verdict="FAIL_PARSE")
        return rec
    rec["parse_ok"] = True
    comp_formula = rdMolDescriptors.CalcMolFormula(mol)
    rec["formula_computed"] = comp_formula
    ok = True
    if expected_formula:
        f_ok = formula_ok(comp_formula, expected_formula)
        rec["formula_expected"] = expected_formula
        rec["formula_match"] = f_ok
        ok = ok and f_ok
    if mz is not None:
        if ion not in ION_ADJUST:
            rec["verdict"] = f"FAIL_UNSUPPORTED_ION({ion})"
            return rec
        mass = rdMolDescriptors.CalcExactMolWt(mol) + ION_ADJUST[ion]
        delta = mass - mz
        rec.update(ion=ion, mz_reported=mz, mz_computed=round(mass, 4),
                   delta_mda=round(delta * 1000, 2),
                   delta_ppm=round(delta / mz * 1e6, 2))
        m_ok = abs(delta) <= tol_da
        rec["mass_match"] = m_ok
        ok = ok and m_ok
    if depict:
        import os
        parent = os.path.dirname(os.path.abspath(depict))
        os.makedirs(parent, exist_ok=True)
        Draw.MolToFile(mol, depict, size=(900, 400))
        rec["depiction"] = depict
    rec["verdict"] = "PASS" if ok else "FAIL_MISMATCH"
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smiles", help="single SMILES to check")
    ap.add_argument("--name", default="compound")
    ap.add_argument("--formula", help="expected molecular formula, e.g. C18H17BF2N2")
    ap.add_argument("--ion", choices=sorted(ION_ADJUST), help="ion species for m/z check")
    ap.add_argument("--mz", type=float, help="reported HRMS m/z")
    ap.add_argument("--depict", help="write 2D depiction PNG to this path")
    ap.add_argument("--batch", help="CSV: name,smiles,formula,ion,mz (formula/ion/mz optional)")
    ap.add_argument("--tol-da", type=float, default=0.01, help="m/z tolerance in Da (default 0.01)")
    ap.add_argument("--json-report", help="write JSON report to this path")
    args = ap.parse_args()

    jobs = []
    if args.batch:
        with open(args.batch, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                jobs.append(dict(
                    name=row.get("name") or "compound",
                    smiles=row["smiles"],
                    expected_formula=row.get("formula") or None,
                    ion=row.get("ion") or None,
                    mz=float(row["mz"]) if row.get("mz") else None,
                ))
    elif args.smiles:
        jobs.append(dict(name=args.name, smiles=args.smiles,
                         expected_formula=args.formula, ion=args.ion,
                         mz=args.mz, depict=args.depict))
    else:
        ap.error("provide --smiles or --batch")

    results = [verify_one(tol_da=args.tol_da, **j) for j in jobs]
    for r in results:
        line = f"{r['name']}: {r['verdict']}"
        if r.get("formula_match") is not None:
            line += f"  formula {r.get('formula_computed')} vs {r.get('formula_expected')}"
        if r.get("mass_match") is not None:
            line += f"  mz {r.get('mz_computed')} vs {r.get('mz_reported')} ({r.get('delta_mda')} mDa, {r.get('delta_ppm')} ppm)"
        print(line)

    report = {"n": len(results),
              "n_pass": sum(1 for r in results if r["verdict"] == "PASS"),
              "results": results}
    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    sys.exit(0 if report["n_pass"] == report["n"] else 1)


if __name__ == "__main__":
    main()

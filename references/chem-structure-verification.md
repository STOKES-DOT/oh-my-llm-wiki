# Chemical Structure Recognition and Verification Workflow

Status: standard operating procedure. Apply to **every** literature-reading
task that involves molecular structures (dyes, oligomers, building blocks).
Designed so that multiple papers can be processed in parallel by subagents.

Companion tool: `scripts/chem_structure_verify.py` (requires `rdkit`).
Worked example: `scripts/examples/build_oligobodipy_example.py`
(thiophene-fused oligo-BODIPYs, JACS 2025, 10.1021/jacs.5c05873).

## Purpose

Convert scheme figures in a paper into machine-readable, **hard-validated**
structures (canonical SMILES), so that downstream knowledge entries
(Molecule Cards, databases, generative design) never rest on unverified
hand-drawn connectivity.

The hard validator is always the paper's own analytical data:
molecular formula and HRMS m/z from the SI. A structure that does not match
the reported formula/mass within tolerance is wrong or the assignment is
wrong; fix before recording.

## Prerequisites

- Python with `rdkit` (project venv or bundled runtime).
- Poppler `pdftoppm` for page rendering.
- The paper PDF and its SI PDF.

## Pipeline (per paper)

### Step 1. Locate scheme pages and characterization data

- Extract full text of main + SI (page-marked). Find Schemes with molecular
  structures and the SI synthesis section with per-compound HRMS entries.
- **Pitfall:** pdfplumber text extraction silently drops subscript formatting,
  so formulas appear as `C H B Cl F N S` with numbers on the next line or
  scrambled. Reconstruct subscripts from reading order, then sanity-check the
  reconstructed formula against the reported m/z before trusting it.

### Step 2. Render scheme pages at high DPI

    pdftoppm -png -r 300 -f <page> -l <page> paper.pdf scheme

300 dpi is the minimum for reading fusion positions, substituent locants and
heteroatom labels. Crop/zoom further when rings are crowded.

### Step 3. Identify connectivity (visual reading)

For each compound record: core scaffold, fusion/substitution positions,
linkers (passive vs bridging atom vs fused ring), end groups, charges/counter
ions if any. For homologous series, first crack the **construction rule**
(repeat unit + connection rule + end groups) instead of reading each
structure in isolation; the rule is then falsifiable against every formula in
the series.

Naming rules matter. Example (oligo-BODIPYs): `nS-FX` turned out to mean
"n unclosed single-S bridges remain"; this was proven by atom-budget
arithmetic on the formula series (each S bridge = -2H vs fused; each
cyclization = -2H). Always do this arithmetic: parent formula + expected
transformations must reproduce the reported formula exactly.

### Step 4. Propose SMILES

- Single compounds: write SMILES directly.
- Homologous series: assemble programmatically with RDKit `RWMol`
  (see the worked example). Define one unit with labeled connection points,
  then add bridges/fusions/substituents per the construction rule.
- **Pitfall (boron):** tetravalent B (BF2, 4 bonds) must be written `[B-]`;
  a neutral `B` with 4 bonds fails sanitization.
- **Pitfall (dative N):** the N->B coordination in BODIPY-type systems needs
  `[N+]`; write one Kekule form and let RDKit canonicalize.
- **Pitfall (valence):** `Can't kekulize` after assembly almost always means
  a topology error, e.g. one sp2 carbon given both a bridge and a fusion
  substituent (4 sigma bonds). Check that each connection point is used once.

### Step 5. Validate against HRMS (hard gate)

Single compound:

    python scripts/chem_structure_verify.py --smiles "<SMILES>" \
        --formula C36H28B2Cl2F4N4S --ion "[M+Na]+" --mz 739.1426 --depict FD.png

Batch (preferred for a whole paper, and for parallel subagents):

    python scripts/chem_structure_verify.py --batch compounds.csv --json-report report.json

CSV columns: `name, smiles, formula, ion, mz` (formula/ion/mz optional but
provide them whenever the SI reports them).

Exit code 0 = all PASS; 1 = at least one FAIL; 2 = rdkit missing.

### Step 6. Visual cross-check

Render every proposed structure (`--depict` or the example script) and
compare against the scheme image: fusion positions, substituent locants,
linker identity, end groups. Formula matching cannot distinguish positional
isomers; this step can.

### Step 7. Record with provenance

In the knowledge entry for each molecule record:

- canonical SMILES (from RDKit, never retyped by hand);
- `extraction_method = agent_from_scheme`;
- `verification = hrms_formula_and_mass` with the delta (mDa / ppm) and the
  ion species used;
- data grade upgrade (e.g. Silver -> Gold at the structure layer);
- any unresolved structures kept as `pending` with the reason.

## Pitfalls and lessons (accumulate new ones here)

1. **Ion species conventions vary within one paper.** Small molecules may be
   reported as [M]+., [M+Na]+ or [M-F]+ while large oligomers' "calcd [M]+"
   actually equals [M+H]+ (a full 1.008 Da off). If the mass is off by ~1 Da,
   try [M+H]+ before doubting the structure. Supported ions are listed in
   `chem_structure_verify.py --help`.
2. **Isotope convention:** instrument "calcd" values usually use most-abundant
   isotopes (11B, 35Cl), matching RDKit `CalcExactMolWt` defaults. Do not mix
   with lightest-isotope monoisotopic masses (10B shifts ~1 Da per B).
3. **Tolerance:** MALDI-TOF calcd vs computed typically agrees within
   0.5-3 mDa (1-3 ppm); use --tol-da 0.01 default, tighten for FT-ICR.
4. **Alternating orientation in oligomers:** arc-shaped fused oligomers
   alternate unit orientation; topologically irrelevant for SMILES validity
   but keep it in mind for the visual cross-check and for 3D work.
5. **Each side once:** in bridged/fused series, a given outer position hosts
   either a bridge, a fusion, or a terminal substituent - never two. Violation
   surfaces as kekulization failure (see Step 4).
6. **Construction-rule arithmetic is the fastest falsifier:** before any
   SMILES work, verify that `repeat unit x n + bridges + end groups - lost H`
   reproduces every reported formula in the series. If it fails, the assumed
   connectivity rule is wrong.

## Parallel / subagent usage

The pipeline is embarrassingly parallel at paper granularity:

- Assign one paper (main + SI) per worker. Each worker produces:
  `compounds.csv`, `report.json`, depiction PNGs, and a short markdown note
  with the construction rule and any pending structures.
- Inputs are independent (separate PDFs, separate output dirs); the only
  shared artifact is the knowledge base, updated after each worker returns.
- A worker must not record a structure that did not PASS Step 5; pending
  structures are reported, not guessed.
- After workers finish, the coordinator cross-checks for duplicate
  Molecule_ID assignments and merges.

## Maintenance

- When a new pitfall is discovered in a project, append it to the pitfalls
  list above (with date and one-line context), so all future literature
  reading benefits.
- Worked examples for new scaffold families should be added under
  `scripts/examples/` following the `build_<family>_example.py` naming.

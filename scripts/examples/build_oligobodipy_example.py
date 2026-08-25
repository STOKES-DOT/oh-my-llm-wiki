# -*- coding: utf-8 -*-
"""Worked example for references/chem-structure-verification.md:
build thiophene-fused oligo-BODIPY SMILES (FD, FT, ...) from the BODIPY core,
validate formula & exact mass against SI HRMS (JACS 2025,
10.1021/jacs.5c05873), and render 2D depictions.

Demonstrates the RWMol assembly pattern for homologous series:
one unit with labeled connection points + bridges/fusions/substituents
added per the construction rule. Adapt `UNIT`, `get_points`, and the
build() calls for other scaffold families."""
from rdkit import Chem
from rdkit.Chem import RWMol, rdMolDescriptors, Draw

# mesityl = 2,4,6-trimethylphenyl, attached at position 1
MESITYL = "c1c(C)cc(C)cc1C"
# BODIPY core (Kekule form; ring1 N = pyrrole-like, ring2 N = [N+], B auto [B-])
UNIT = "F[B-]1(F)N2C=CC=C2C(=C2C=CC=[N+]12)" + MESITYL


def get_points(unit):
    """Return dict of key atom indices for one BODIPY unit."""
    b = next(a for a in unit.GetAtoms() if a.GetSymbol() == "B")
    ns = [a for a in b.GetNeighbors() if a.GetSymbol() == "N"]
    n_neutral = next(n for n in ns if n.GetFormalCharge() == 0)
    n_plus = next(n for n in ns if n.GetFormalCharge() == 1)
    # meso C: neighbor of n_neutral... find carbon bonded to mesityl ipso
    meso = None
    for a in unit.GetAtoms():
        if a.GetSymbol() != "C" or a.GetIsAromatic():
            continue
        nb = a.GetNeighbors()
        if len(nb) == 3 and sum(1 for x in nb if x.GetIsAromatic()) == 1:
            meso = a
            break

    def outer_alpha(n):
        # C neighbor of n that is NOT bonded to meso
        for c in n.GetNeighbors():
            if c.GetSymbol() == "C" and meso not in c.GetNeighbors():
                return c
        raise RuntimeError("no outer alpha")

    oa1 = outer_alpha(n_neutral)
    oa2 = outer_alpha(n_plus)

    def beta(oa, n):
        for c in oa.GetNeighbors():
            if c.GetSymbol() == "C" and c.GetIdx() != n.GetIdx():
                return c
        raise RuntimeError("no beta")

    return {
        "oa1": oa1.GetIdx(), "b1": beta(oa1, n_neutral).GetIdx(),
        "oa2": oa2.GetIdx(), "b2": beta(oa2, n_plus).GetIdx(),
    }


def build(n_units, fused_links, s_bridges, cl_terminals):
    """Assemble oligomer.

    fused_links: list of (unit_i, side_i, unit_j, side_j) with full thiophene fusion
                 (S between outer alphas + C-C between betas).
    s_bridges:   same, but only the S bridge (no C-C bond).
    cl_terminals: list of (unit_i, side) to chlorinate (side 1 or 2).
    """
    unit = Chem.MolFromSmiles(UNIT)
    assert unit is not None, "unit SMILES failed to parse"
    pts = get_points(unit)

    combo = unit
    offsets = [0]
    for i in range(1, n_units):
        offsets.append(combo.GetNumAtoms())
        combo = Chem.CombineMols(combo, unit)
    rw = RWMol(combo)

    def idx(u, key):
        return offsets[u] + pts[key]

    def add_atom(sym):
        a = Chem.Atom(sym)
        return rw.AddAtom(a)

    for (i, si, j, sj) in s_bridges:
        s = add_atom("S")
        rw.AddBond(idx(i, f"oa{si}"), s, Chem.BondType.SINGLE)
        rw.AddBond(s, idx(j, f"oa{sj}"), Chem.BondType.SINGLE)
    for (i, si, j, sj) in fused_links:
        s = add_atom("S")
        rw.AddBond(idx(i, f"oa{si}"), s, Chem.BondType.SINGLE)
        rw.AddBond(s, idx(j, f"oa{sj}"), Chem.BondType.SINGLE)
        rw.AddBond(idx(i, f"b{si}"), idx(j, f"b{sj}"), Chem.BondType.SINGLE)
    for (i, si) in cl_terminals:
        cl = add_atom("Cl")
        rw.AddBond(idx(i, f"oa{si}"), cl, Chem.BondType.SINGLE)

    mol = rw.GetMol()
    Chem.SanitizeMol(mol)
    return mol


def report(name, mol, expected_formula, hrms_note, img):
    f = rdMolDescriptors.CalcMolFormula(mol)
    mass = rdMolDescriptors.CalcExactMolWt(mol)
    ok = (f == expected_formula)
    print(f"{name}: formula {f} (expected {expected_formula}) -> {'MATCH' if ok else 'MISMATCH'}")
    print(f"   exact mass (most abundant isotopes): {mass:.4f}   HRMS: {hrms_note}")
    print(f"   canonical: {Chem.MolToSmiles(mol)}")
    Draw.MolToFile(mol, img, size=(900, 400))
    return ok


def main():
    # sanity: monomer M
    m = Chem.MolFromSmiles(UNIT)
    report("M", m, "C18H17BF2N2", "literature compound", "structures_out/M.png")

    # SD: 2 units, one S bridge (side1-side1), no Cl
    sd = build(2, fused_links=[], s_bridges=[(0, 1, 1, 1)], cl_terminals=[])
    report("SD", sd, "C36H32B2F4N4S", "[M-F]+ calcd 631.2480", "structures_out/SD.png")

    # SD-2Cl: S bridge + 2 terminal Cl (side2 each)
    sd2cl = build(2, fused_links=[], s_bridges=[(0, 1, 1, 1)], cl_terminals=[(0, 2), (1, 2)])
    report("SD-2Cl", sd2cl, "C36H30B2Cl2F4N4S", "[M-F]+ calcd 699.1701", "structures_out/SD-2Cl.png")

    # FD: thiophene fusion between the two units + 2 terminal Cl
    fd = build(2, fused_links=[(0, 1, 1, 1)], s_bridges=[], cl_terminals=[(0, 2), (1, 2)])
    report("FD", fd, "C36H28B2Cl2F4N4S", "[M+Na]+ calcd 739.1426", "structures_out/FD.png")

    # 1S-FT: 4 units; fused thiophenes A-B and C-D; middle S bridge B-C; Cl on A.side2, D.side2
    sft = build(4, fused_links=[(0, 1, 1, 1), (2, 2, 3, 1)],
                s_bridges=[(1, 2, 2, 1)], cl_terminals=[(0, 2), (3, 2)])
    report("1S-FT", sft, "C72H56B4Cl2F8N8S3", "[M]+ calcd 1394.3445", "structures_out/1S-FT.png")

    # FT: 4 units, 3 fused thiophenes, 2 terminal Cl
    ft = build(4, fused_links=[(0, 1, 1, 1), (1, 2, 2, 1), (2, 2, 3, 1)],
               s_bridges=[], cl_terminals=[(0, 2), (3, 2)])
    report("FT", ft, "C72H54B4Cl2F8N8S3", "[M]+ calcd 1392.3289", "structures_out/FT.png")

    # FH: 6 units, 5 fused thiophenes, 2 terminal Cl
    fh = build(6, fused_links=[(0, 1, 1, 1), (1, 2, 2, 1), (2, 2, 3, 1), (3, 2, 4, 1), (4, 2, 5, 1)],
               s_bridges=[], cl_terminals=[(0, 2), (5, 2)])
    report("FH", fh, "C108H80B6Cl2F12N12S5", "[M]+ calcd 2069.5030", "structures_out/FH.png")

    # FO: 8 units, 7 fused thiophenes, 2 terminal Cl
    fo = build(8, fused_links=[(0, 1, 1, 1), (1, 2, 2, 1), (2, 2, 3, 1), (3, 2, 4, 1),
                               (4, 2, 5, 1), (5, 2, 6, 1), (6, 2, 7, 1)],
               s_bridges=[], cl_terminals=[(0, 2), (7, 2)])
    report("FO", fo, "C144H106B8Cl2F16N16S7", "[M]+ calcd 2745.6774", "structures_out/FO.png")

    # 2S-FH: 3 FD blocks + 2 S bridges
    sfh = build(6, fused_links=[(0, 1, 1, 1), (2, 1, 3, 1), (4, 1, 5, 1)],
                s_bridges=[(1, 2, 2, 2), (3, 2, 4, 2)], cl_terminals=[(0, 2), (5, 2)])
    report("2S-FH", sfh, "C108H84B6Cl2F12N12S5", "[M]+ calcd 2073.5343", "structures_out/2S-FH.png")

    # 3S-FO: 4 FD blocks + 3 S bridges
    sfo3 = build(8, fused_links=[(0, 1, 1, 1), (2, 1, 3, 1), (4, 1, 5, 1), (6, 1, 7, 1)],
                 s_bridges=[(1, 2, 2, 2), (3, 2, 4, 2), (5, 2, 6, 2)], cl_terminals=[(0, 2), (7, 2)])
    report("3S-FO", sfo3, "C144H112B8Cl2F16N16S7", "[M]+ calcd 2751.7244", "structures_out/3S-FO.png")

    # 1S-FO: 2 FT blocks + 1 S bridge
    sfo1 = build(8, fused_links=[(0, 1, 1, 1), (1, 2, 2, 1), (2, 2, 3, 1),
                                 (4, 1, 5, 1), (5, 2, 6, 1), (6, 2, 7, 1)],
                 s_bridges=[(3, 2, 4, 2)], cl_terminals=[(0, 2), (7, 2)])
    report("1S-FO", sfo1, "C144H108B8Cl2F16N16S7", "[M]+ calcd 2747.6930", "structures_out/1S-FO.png")


if __name__ == "__main__":
    import os
    os.makedirs(r"structures_out", exist_ok=True)
    main()



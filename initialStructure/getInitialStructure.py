import numpy as np
import subprocess
# ----- user data -------------------------------------------------------------
molar_masses = {"Li": 6.9410, "Ta": 180.94788, "Cl": 35.45}     # g mol⁻¹
stoich       = {"Li": 1, "Ta": 1, "Cl": 6}                      # LiTaCl₆
density      = 2.96                      # g cm⁻³
box_diam     = 12.0                      # Å
# ---------------------------------------------------------------------------

# Write pdb files for packmol input
pdbTemplate = (
    "HETATM    1  {el:<2}  {el} A   1       0.000   0.000   0.000  1.00  0.00          {el:>2}\n"
    "END\n"
)

for el in stoich.keys():
    with open(f"{el}.pdb", "w") as f:
        f.write(pdbTemplate.format(el=el))
        print(f"Wrote {el}.pdb")
NA           = 6.022_140_76e23           # mol⁻¹  (exact) 
# 1. mass of one formula unit
M_formula = sum(molar_masses[e] * n for e, n in stoich.items())   # g/mol

# 2. volume of the simulation region (cm³)
V_cm3 = (box_diam**3) * 1e-24             # Å³ → cm³



# 3. number of formula units that match the target density
m_sample   = density * V_cm3                 # g
n_moles    = m_sample / M_formula            # mol
n_formula  = n_moles * NA                    # dimensionless
n_formula_rounded = int(n_formula + 1)  # closest whole molecule

# 4. atoms per element
atom_counts = {e: n * n_formula_rounded for e, n in stoich.items()}

# 4. compute exact diameter using the number of formula
n_moles_exact = n_formula_rounded / NA
V_cm3_exact = n_moles_exact * M_formula / density
box_diam_exact = (V_cm3_exact * 1e24)**(1/3)  # cm³ → Å³

print(f"Formula units     : {n_formula_rounded:.2f}")
print(f"Box diameter     : {box_diam_exact:.16f} Å")
print("Atoms to place   :")
for e, n in atom_counts.items():
    print(f"  {e}: {n:.2f}")

# write the information to init.inp
with open("init.inp", "w") as f:
    f.write(f"tolerance 2.0\n")
    f.write("filetype pdb\n")
    f.write(f"pbc {box_diam_exact:.16f} {box_diam_exact:.16f} {box_diam_exact:.16f}\n")
    f.write(f"output init.pdb\n\n")

    for element in stoich.keys():
        f.write(f"structure {element}.pdb\n")
        f.write(f"  number {atom_counts[element]}\n")
        f.write("end structure\n\n")

print(f"Packmol input written to init.inp")

# use packmol to generate an initial structure
subprocess.call("/pscratch/sd/x/xlliu9/Software/packmol/packmol < init.inp", shell=True)

# convert the init.pdb to VASP POSCAR format
from ase.io import read, write
atoms = read("init.pdb")
atoms.set_cell([box_diam_exact, box_diam_exact, box_diam_exact])
atoms.set_pbc([True, True, True])
write("POSCAR", atoms, format="vasp")

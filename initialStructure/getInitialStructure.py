import numpy as np

# ----- user data -------------------------------------------------------------
molar_masses = {"Li": 6.9410, "Ta": 180.94788, "Cl": 35.45}     # g mol⁻¹
stoich       = {"Li": 1, "Ta": 1, "Cl": 6}                      # LiTaCl₆
density      = 2.96                      # g cm⁻³
box_diam     = 12.0                      # Å
NA           = 6.022_140_76e23           # mol⁻¹  (exact) 
# ---------------------------------------------------------------------------

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



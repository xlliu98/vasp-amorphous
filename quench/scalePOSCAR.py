import numpy as np
import sys

# Atom info
molar_masses = {"Li": 6.9410, "Ta": 180.94788, "Cl": 35.45}     # g mol⁻¹
stoich       = {"Li": 1, "Ta": 1, "Cl": 6}                      # LiTaCl₆
units = 8  # Number of formula units per POSCAR

# Constants
bulk = 100  # GPa, estimated bulk modulus
M_formula = sum(molar_masses[e] * n for e, n in stoich.items())   # g/mol

def scalePOSCAR(filePath, pressure_kbar):
    # Convert pressure (kbar) to scaling factor
    p_GPa = pressure_kbar / 10.0
    scale = (1 + p_GPa / bulk) ** (1 / 3)

    # Read POSCAR
    lines = []
    with open(filePath, 'r') as f:
        for line in f:
            if line.strip() == "":
                break  # stop at first empty or whitespace-only line, for MD CONTCAR
            lines.append(line)

    # Parse lattice
    lattice = []
    for l in range(2, 5):
        lattice.extend([float(x) for x in lines[l].split()])
    lattice = np.array(lattice).reshape((3, 3))

    # Apply scaling (only diagonal, isotropic)
    for i in range(3):
        lattice[i][i] *= scale

    # Density estimate (assumes cubic)
    volume_A3 = np.linalg.det(lattice)
    density = mass / (6.022e23 * volume_A3 * 1e-24)  # g/cm^3

    print(f"Applied scale = {scale:.8f}")
    print(f"Estimated density = {density:.4f} g/cm^3")

    # Update POSCAR lattice lines
    for i in range(3):
        lines[2 + i] = "  " + "  ".join(f"{x:.16f}" for x in lattice[i]) + "\n"

    with open("POSCAR_scaled", "w") as f:
        f.writelines(lines)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scalePOSCAR.py <POSCAR_path> <pressure_kbar>")
        sys.exit(1)

    filePath = sys.argv[1]
    try:
        pressure_kbar = float(sys.argv[2])
    except ValueError:
        print("Error: pressure must be a number (in kBar)")
        sys.exit(1)

    scalePOSCAR(filePath, pressure_kbar)


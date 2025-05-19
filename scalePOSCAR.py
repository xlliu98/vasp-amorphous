import numpy as np
import sys

def scalePOSCAR(filePath, scale):

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


    # Update POSCAR lattice lines
    for i in range(3):
        lines[2 + i] = "  " + "  ".join(f"{x:.16f}" for x in lattice[i]) + "\n"

    with open("POSCAR_scaled", "w") as f:
        f.writelines(lines)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scalePOSCAR.py <POSCAR_path> <scale>")
        sys.exit(1)

    filePath = sys.argv[1]
    try:
        scale = float(sys.argv[2])
    except ValueError:
        print("Error: scale must be a number")
        sys.exit(1)

    scalePOSCAR(filePath, scale)


